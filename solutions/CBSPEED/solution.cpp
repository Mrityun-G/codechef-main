#include <bits/stdc++.h>
using namespace std;

/**
 * Problem Analysis:
 * The problem asks us to compare two integers X (threshold) and Y (current speed).
 * Chef is prone to errors if Y > X.
 * 
 * Constraints:
 * 1 <= X, Y <= 100
 * Time Complexity: O(1) per test case.
 * Space Complexity: O(1).
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int X, Y;
    // Reading the two integers X and Y
    if (cin >> X >> Y) {
        // If current speed Y is strictly greater than threshold X, print YES
        if (Y > X) {
            cout << "YES" << "\n";
        } else {
            // Otherwise, print NO
            cout << "NO" << "\n";
        }
    }

    return 0;
}