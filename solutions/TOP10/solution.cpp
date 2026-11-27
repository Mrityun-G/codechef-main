#include <bits/stdc++.h>
using namespace std;

/**
 * Problem Analysis:
 * Chef is ranked X. We need to determine if X <= 10.
 * If X <= 10, output YES.
 * Otherwise, output NO.
 * 
 * Constraints:
 * 1 <= T <= 100
 * 1 <= X <= 100
 * Time Complexity: O(T)
 * Space Complexity: O(1)
 */

int main() {
    // Optimize standard I/O operations for competitive programming
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;
    
    while (t--) {
        long long x;
        cin >> x;
        
        // Check if the rank is within the top 10
        if (x <= 10) {
            cout << "YES" << "\n";
        } else {
            cout << "NO" << "\n";
        }
    }
    
    return 0;
}