import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/answer_format.dart';

void main() {
  group('looksLikeMarkdown (109/FR-006, research.md R3)', () {
    test('true for a closed fenced code block', () {
      expect(looksLikeMarkdown('here:\n```\ninterface Gi0/1 up\n```\ndone'), isTrue);
    });

    test('true for a pipe-table row', () {
      expect(looksLikeMarkdown('Name | State\neth0 | up'), isTrue);
    });

    test('false for bare CLI output containing #, *, _, | with no fence or table row', () {
      const cli = 'interface GigabitEthernet0/1\n'
          ' description uplink_to_core # primary\n'
          ' ip address 10.0.0.1/24\n'
          ' * this line has an asterisk\n'
          ' snake_case_var=1\n'
          'a trailing pipe |';
      expect(looksLikeMarkdown(cli), isFalse);
    });

    test('false for plain text', () {
      expect(looksLikeMarkdown('BGP is up on the core switch.'), isFalse);
    });
  });
}
