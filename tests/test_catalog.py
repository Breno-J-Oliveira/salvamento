import base64
import hashlib
import sqlite3
import unittest

from catalog import CATALOG, caesar, seed_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        self.connection.execute('CREATE TABLE challenges(id INTEGER PRIMARY KEY,title TEXT,category TEXT,side TEXT,points INTEGER,description TEXT,hint TEXT,url TEXT,flag_hash TEXT)')

    def tearDown(self):
        self.connection.close()

    def test_incremental_seed_preserves_existing_challenge(self):
        self.connection.execute("INSERT INTO challenges(id,title,flag_hash) VALUES(4,'Cifra de César','custom-hash')")
        seed_catalog(self.connection)
        seed_catalog(self.connection)
        self.assertEqual(self.connection.execute('SELECT COUNT(*) FROM challenges').fetchone()[0],8)
        self.assertEqual(self.connection.execute("SELECT id,flag_hash FROM challenges WHERE title='Cifra de César'").fetchone(),(4,'custom-hash'))

    def test_answers_match_persisted_hashes(self):
        seed_catalog(self.connection)
        for item in CATALOG:
            with self.subTest(title=item['title']):
                row=self.connection.execute('SELECT flag_hash FROM challenges WHERE title=?',(item['title'],)).fetchone()
                self.assertEqual(row[0],hashlib.sha256(item['answer'].encode()).hexdigest())
                self.assertTrue(item['answer'].startswith('CTF{'))
                self.assertGreater(item['points'],0)

    def test_puzzles_decode_to_declared_answers(self):
        caesar_item=CATALOG[0]
        self.assertEqual(caesar(caesar_item['description'].split('\n\n')[-1],-3),caesar_item['answer'])
        layered=CATALOG[1]
        self.assertEqual(base64.b64decode(base64.b64decode(layered['description'].split('\n\n')[-1])).decode(),layered['answer'])
        self.assertEqual('CTF{'+''.join(map(chr,[112,117,114,112,108,101,50,48,50,54]))+'}',CATALOG[2]['answer'])

    def test_titles_unique_and_seeded_order_stable(self):
        self.assertEqual(len({item['title'] for item in CATALOG}),8)
        seed_catalog(self.connection)
        self.assertEqual([row[0] for row in self.connection.execute('SELECT title FROM challenges ORDER BY id')],[item['title'] for item in CATALOG])

if __name__=='__main__':unittest.main()
