#include <bits/stdc++.h>
using namespace std;

/**
 * Problem Analysis:
 * The problem asks for the number of unattempted problems given the total number of problems (X)
 * and the number of attempted problems (Y).
 * The number of unattempted problems is simply X - Y.
 * 
 * Constraints:
 * 1 <= Y <= X <= 1000
 * Since the values are small, standard 'int' is sufficient, but 'long long' is used 
 * for good practice in competitive programming to prevent overflow in larger variations.
 * Time Complexity: O(1) per test case.
 * Space Complexity: O(1).
 */

int main() {
    // Optimize standard I/O operations for speed
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long X, Y;
    
    // Read the input values X and Y
    if (cin >> X >> Y) {
        // Calculate the difference
        long long unattempted = X - Y;
        
        // Output the result
        cout << unattempted << "\n";
    }

    return 0;
}