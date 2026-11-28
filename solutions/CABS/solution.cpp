#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: The Cheaper Cab
 * Approach: Compare the two integers X and Y.
 * Time Complexity: O(T) where T is the number of test cases.
 * Space Complexity: O(1) as we only use a few variables.
 */

int main() {
    // Optimize I/O operations
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;
    
    while (t--) {
        long long x, y;
        cin >> x >> y;
        
        if (x < y) {
            cout << "FIRST" << "\n";
        } else if (y < x) {
            cout << "SECOND" << "\n";
        } else {
            cout << "ANY" << "\n";
        }
    }
    
    return 0;
}