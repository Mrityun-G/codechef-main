#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: ATM (HS08TEST)
 * Logic:
 * 1. Check if X is a multiple of 5 (X % 5 == 0).
 * 2. Check if the withdrawal amount + 0.50 is less than or equal to the balance Y.
 * 3. If both conditions are met, subtract (X + 0.50) from Y.
 * 4. Otherwise, print the original balance Y.
 * 5. Format output to 2 decimal places.
 */

int main() {
    // Fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int X;
    double Y;

    // The problem statement implies a single test case per run based on the 
    // provided sample format, but we read X and Y.
    if (!(cin >> X >> Y)) return 0;

    // Set output precision to 2 decimal places
    cout << fixed << setprecision(2);

    // Condition 1: X must be a multiple of 5
    // Condition 2: X + 0.50 must be <= Y
    if ((X % 5 == 0) && (static_cast<double>(X) + 0.50 <= Y)) {
        Y = Y - (static_cast<double>(X) + 0.50);
        cout << Y << "\n";
    } else {
        // Transaction failed, print original balance
        cout << Y << "\n";
    }

    return 0;
}