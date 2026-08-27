import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/edge_client.dart';
import 'package:netclaw_mobile/ncfed/pending_approvals_headless.dart';

class _FakeRpc implements EdgeRpcSource {
  final Map<String, dynamic> response;
  _FakeRpc(this.response);

  @override
  void on(String method, EdgeMethodHandler handler) {}

  @override
  Future<Map<String, dynamic>> call(String method, Map<String, dynamic> params,
      {Duration timeout = const Duration(seconds: 30)}) async {
    expect(method, 'n2n/edge/approvals_list');
    return response;
  }
}

void main() {
  test('speaks the live count when approvals are pending (FR-006)', () async {
    final spoken = await runPendingApprovals(_FakeRpc({'count': 3}));
    expect(spoken, '3 approvals are pending.');
  });

  test('uses singular phrasing for exactly one pending approval', () async {
    final spoken = await runPendingApprovals(_FakeRpc({'count': 1}));
    expect(spoken, '1 approval is pending.');
  });

  test('speaks an explicit statement for zero, not a bare "0" (FR-006)', () async {
    final spoken = await runPendingApprovals(_FakeRpc({'count': 0}));
    expect(spoken, 'No approvals are pending.');
  });
}
