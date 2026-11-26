#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: Greater Average
 * The condition is: (A + B) / 2 > C
 * To avoid floating point precision issues, we can multiply both sides by 2:
 * A + B > 2 * C
 * This allows us to work entirely with integers.
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;

    while (t--) {
        long long a, b, c;
        cin >> a >> b >> c;

        // Check if (a + b) / 2 > c
        // Equivalent to (a + b) > 2 * c
        if ((a + b) > (2 * c)) {
            cout << "YES" << "\n";
        } else {
            cout << "NO" << "\n";
        }
    }

    return 0;
}