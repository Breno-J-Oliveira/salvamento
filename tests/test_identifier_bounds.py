import os
import tempfile
import unittest
os.environ.setdefault('SECRET_KEY','test-only-identifier-bounds')
import app as module


class IdentifierBoundsTests(unittest.TestCase):
    def test_oversized_identifiers_return_not_found_without_database_overflow(self):
        with tempfile.TemporaryDirectory() as folder:
            old=module.DB
            try:
                module.DB=os.path.join(folder,'identifiers.db')
                module.app.config['TESTING']=True
                module.init_db()
                client=module.app.test_client()
                with client.session_transaction() as session:session['user_id']=1
                huge='9'*40
                for route in ['/admin/assessments/assignments/'+huge,
                              '/admin/challenges/'+huge+'/edit',
                              '/challenge/'+huge,
                              '/my-applications/'+huge+'/receipt',
                              '/remote-labs/'+huge]:
                    self.assertEqual(client.get(route).status_code,404,route)
            finally:
                module.DB=old


if __name__=='__main__':unittest.main()
