#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: Find Remainder (FLOW002)
 * Time Complexity: O(T), where T is the number of test cases.
 * Space Complexity: O(1), as we only use a few variables for calculation.
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;

    while (t--) {
        long long a, b;
        if (cin >> a >> b) {
            // The remainder is calculated using the modulo operator (%)
            // Constraints: 1 <= A, B <= 10000, so long long is sufficient.
            cout << (a % b) << "\n";
        }
    }

    return 0;
}