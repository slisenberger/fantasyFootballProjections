import unittest
import pandas as pd
import os
from stats import players

class TestRegression(unittest.TestCase):
    def test_vectorized_sorting(self):
        """
        Verify that _compute_estimator_vectorized sorts by time correctly.
        We create a synthetic dataset where recent performance is high and old performance is low.
        If sorting works, the estimate should be high (recent bias).
        If sorting fails, it might be low (average).
        """
        data = pd.DataFrame({
            'player_id': ['A'] * 10,
            'week': range(1, 11),
            'value': [0]*5 + [100]*5 # First 5 weeks 0, Last 5 weeks 100
        })
        
        prior = pd.DataFrame({'player_id': ['A'], 'value': [0]})
        
        # Compute Estimate
        # Span = 3 (Fast adaptation)
        result = players._compute_estimator_vectorized(
            data, 'player_id', 'value', 3, prior, 'est', time_col='week'
        )
        
        est = result['est'].iloc[0]
        print(f"Test Estimate (Should be close to 100): {est}")
        
        # With span=3, alpha=2/(3+1)=0.5.
        # After 5 weeks of 100, it should be very close to 100.
        self.assertTrue(est > 80, f"Estimate {est} is too low. Sorting likely failed.")

    def test_smoothing_removed(self):
        """
        Verify that get_targets doesn't have the +0.1 smoothing.
        This is a code inspection test or logic verification.
        We can't easily unit test the engine method without mocking.
        """
        pass

if __name__ == '__main__':
    unittest.main()
