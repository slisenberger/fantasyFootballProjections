import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from collections import defaultdict
from main import calculate_fantasy_leaders
from settings import AppConfig

class TestScoringIntegrity(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig() # Defaults
        self.season = 2023
        self.week = 1

    @patch('main.score.score_from_play')
    @patch('main.score.points_from_score')
    def test_nan_poisoning_prevention(self, mock_points_from_score, mock_score_from_play):
        """
        Regression Test for 'Missing Mahomes' Bug.
        Ensures that if score_from_play returns a dict containing NaN keys or values,
        it does not poison the accumulator for other valid keys.
        """
        
        # Mock PBP Data: 2 plays
        # Play 1: Valid score for Player A.
        # Play 2: 'Poison' score (Player A gets valid points, but 'nan' key has 'nan' value).
        
        data = pd.DataFrame({
            'week': [1, 1],
            'season': [2023, 2023],
            'play_type': ['pass', 'pass'],
            'game_id': ['g1', 'g1'],
            'away_team': ['AWAY', 'AWAY'],
            'home_team': ['HOME', 'HOME'],
            'total_away_score': [0, 0],
            'total_home_score': [0, 0]
        })
        
        # Mock Returns
        # Play 1: Player A gets 10.0
        # Play 2: Player A gets 5.0, and 'nan' gets 'nan' (e.g. missing receiver ID)
        mock_score_from_play.side_effect = [
            {'PlayerA': 10.0},
            {'PlayerA': 5.0, float('nan'): float('nan')}
        ]
        
        mock_points_from_score.return_value = 0 # Ignore DST scoring
        
        # Execute
        results = calculate_fantasy_leaders(data, self.season, self.week, self.config)
        
        # Assertions
        # Player A should exist
        self.assertIn('PlayerA', results['player_id'].values)
        
        # Player A score should be 15.0 (10 + 5). Not NaN.
        player_a_score = results.loc[results['player_id'] == 'PlayerA', 'score'].iloc[0]
        self.assertEqual(player_a_score, 15.0)
        
        # NaN key should NOT be in results (dropna filters it, or logic ignores it)
        # If logic ignored it, it's not in scores dict.
        # If logic added it, scores[nan] = nan. dropna removes it.
        # But PlayerA MUST survive.

if __name__ == '__main__':
    unittest.main()
