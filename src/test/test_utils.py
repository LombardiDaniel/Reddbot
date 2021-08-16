import unittest

import utils # pylint: disable=E0401


class TestUtils(unittest.TestCase):
    def test_sub_search_on_msg(self):
        '''
        Tests the check_reddit_embed() function from Utils.
        '''

        # Checks with escape characters
        self.assertEqual(utils.check_reddit_embed(
            'Eu adoro o sub r/memes, /r/dankmemes\n\te tbm uns outros'),
            ['memes', 'dankmemes'])
        # Check reddit sub link
        self.assertEqual(utils.check_reddit_embed(
            'https://www.reddit.com/r/memes/'),
            [])
        # Check reddit post link
        self.assertEqual(utils.check_reddit_embed(
            'https://www.reddit.com/r/memes/comments/nghvge/be_original_original_wednesday_frog_memes_are_not/'), # pylint: disable=C0301
            [])

if __name__ == '__main__':
    unittest.main()
