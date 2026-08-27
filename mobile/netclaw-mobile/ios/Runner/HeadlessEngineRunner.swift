import Flutter
import Foundation
import flutter_secure_storage_darwin
import flutter_local_notifications

/// Errors surfaced to Swift by a headless entrypoint's `submit` reply,
/// classified via `FlutterError.code` so each intent can speak the right
/// distinct failure message (spec 111 FR-008/FR-010).
enum HeadlessIntentError: Error {
    case notEnrolled
    case timedOut
    case noData
    case failed(String)
}

/// Shared plumbing for every headless-engine App Intent (spec 111). Uses a
/// shared `FlutterEngineGroup` rather than a raw second `FlutterEngine`
/// (spec 115/research.md R2) -- a plain `FlutterEngine` created independently
/// of the app's main engine is unsupported when that main engine may still
/// be alive in the same process, which is exactly App Intents'
/// `openAppWhenRun = false` scenario (confirmed on-device: the app process
/// gets thawed/resumed, not launched fresh). Only registers the specific
/// plugins these three entrypoints actually touch
/// (`flutter_secure_storage_darwin`, `flutter_local_notifications`, and the
/// app's own `EdgeIdentityPlugin`) rather than the full
/// `GeneratedPluginRegistrant.register(with:)` sweep, since that also
/// re-registers Firebase Core/Messaging into this second engine while the
/// main engine's own Firebase instance is alive in the same process --
/// confirmed via a pulled on-device crash report as the cause of a real
/// `SIGKILL` (`0x8BADF00D` scene-update watchdog transgression) before this
/// fix. Deterministic teardown (FR-009/research.md R7) happens simply by the
/// owning `AppIntent` releasing its last strong reference to this object
/// once it's done with it — matching how `AppDelegate.swift` tears its own
/// background-refresh engine down by setting `backgroundRefreshEngine =
/// nil`, since `FlutterEngine` has no separate public "destroy" call.
///
/// `FlutterEngine` creation/run MUST happen on the main thread. AppIntents'
/// `perform()` does not guarantee it runs on the main actor, so without this
/// annotation, engine startup could race against (and deadlock with)
/// whatever executor AppIntents chose. Marking the class `@MainActor` makes
/// every call site hop onto the main actor via an implicit `await`,
/// guaranteeing engine work always happens on the thread Flutter requires.
@MainActor
final class HeadlessEngineRunner {
    /// Shared/lazy so repeated intent invocations reuse the same group
    /// rather than re-paying Dart VM setup each time.
    private static let engineGroup = FlutterEngineGroup(name: "netclaw-headless-intents", project: nil)

    private let engine: FlutterEngine
    private let channel: FlutterMethodChannel

    /// [libraryURI] MUST be the entrypoint's real Dart package URI (e.g.
    /// `package:netclaw_mobile/ncfed/border_health_headless.dart`) -- passing
    /// `nil` here silently fails to resolve any entrypoint defined outside
    /// `lib/main.dart` (spec 115/research.md R3), unlike plain
    /// `FlutterEngine.run(withEntrypoint:)`, which resolves by bare name
    /// against the whole compiled program.
    init(entrypoint: String, libraryURI: String, channelName: String) {
        let engine = Self.engineGroup.makeEngine(withEntrypoint: entrypoint, libraryURI: libraryURI)
        // path_provider needs no explicit registration here -- it isn't in
        // GeneratedPluginRegistrant.m either (confirmed), and the main
        // engine's own getApplicationDocumentsDirectory() calls work fine
        // without it, so its Swift implementation self-registers or needs
        // no native plugin class at all in this Flutter version.
        if let registrar = engine.registrar(forPlugin: "FlutterSecureStorageDarwinPlugin") {
            FlutterSecureStorageDarwinPlugin.register(with: registrar)
        }
        if let registrar = engine.registrar(forPlugin: "FlutterLocalNotificationsPlugin") {
            FlutterLocalNotificationsPlugin.register(with: registrar)
        }
        if let registrar = engine.registrar(forPlugin: "EdgeIdentityPlugin") {
            EdgeIdentityPlugin.register(with: registrar)
        }
        self.engine = engine
        self.channel = FlutterMethodChannel(name: channelName, binaryMessenger: engine.binaryMessenger)
    }

    /// Bridges a single Swift-initiated `invokeMethod("submit", ...)` call to
    /// async/await. Dart's handler either returns the spoken/acknowledgment
    /// string directly, or throws a `PlatformException` whose `code` this
    /// classifies into a [HeadlessIntentError]. A local [timeout] backstops a
    /// Dart side that never replies at all (distinct from `headless_connect.
    /// dart`'s own connect-specific timeout, which surfaces as a
    /// `"timeout"`-coded reply, not a silent hang).
    func submit(_ arguments: Any?, timeout: TimeInterval) async throws -> String {
        try await withCheckedThrowingContinuation { continuation in
            var didResume = false
            let resumeOnce: (Result<String, Error>) -> Void = { outcome in
                guard !didResume else { return }
                didResume = true
                continuation.resume(with: outcome)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + timeout) {
                resumeOnce(.failure(HeadlessIntentError.timedOut))
            }
            channel.invokeMethod("submit", arguments: arguments) { reply in
                if let error = reply as? FlutterError {
                    switch error.code {
                    case "not_enrolled":
                        resumeOnce(.failure(HeadlessIntentError.notEnrolled))
                    case "timeout":
                        resumeOnce(.failure(HeadlessIntentError.timedOut))
                    case "no_data":
                        resumeOnce(.failure(HeadlessIntentError.noData))
                    default:
                        resumeOnce(.failure(HeadlessIntentError.failed(error.message ?? "unknown error")))
                    }
                } else if let ack = reply as? String {
                    resumeOnce(.success(ack))
                } else {
                    resumeOnce(.failure(HeadlessIntentError.failed("unexpected response")))
                }
            }
        }
    }

    /// `AskBorderIntent`-only: waits for Dart to proactively call `finished`
    /// on this same channel once its bounded post-acknowledgment window
    /// (research.md R8) resolves (the `ask_result` landed and the
    /// notification was posted, or that window's own internal timeout
    /// elapsed) — capped by this method's own [timeout] as a backstop.
    func waitForFinished(timeout: TimeInterval) async {
        await withCheckedContinuation { continuation in
            var didResume = false
            let resumeOnce: () -> Void = {
                guard !didResume else { return }
                didResume = true
                continuation.resume()
            }
            channel.setMethodCallHandler { call, result in
                if call.method == "finished" {
                    resumeOnce()
                    result(nil)
                } else {
                    result(FlutterMethodNotImplemented)
                }
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + timeout) {
                resumeOnce()
            }
        }
    }
}
