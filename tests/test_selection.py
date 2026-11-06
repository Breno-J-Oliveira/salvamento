import json
import os
import sqlite3
import tempfile
import unittest
import app as module

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=module.DB
        module.DB=os.path.join(self.temp.name,'selection.db');module.app.config['TESTING']=True
        module.RATE_BUCKETS.clear();module.init_db();self.client=module.app.test_client()
        con=sqlite3.connect(module.DB)
        try:
            con.execute("INSERT INTO users(id,name,email,role) VALUES(2,'Pessoa','person@example.test','participante')")
            con.execute("INSERT INTO users(id,name,email,role) VALUES(3,'Outra','other@example.test','participante')")
            con.execute("INSERT INTO jobs(id,title,company,description,side,min_points,active) VALUES(1,'SOC','Demo','Descrição de teste','Blue Team',0,1)")
            con.execute("INSERT INTO applications(id,job_id,user_id,status,created_at) VALUES(1,1,2,'submitted',1)")
            con.commit()
        finally:con.close()
        self.as_user(2)
    def tearDown(self):
        module.DB=self.old;self.temp.cleanup()
    def as_user(self,uid):
        with self.client.session_transaction() as s:s.update(user_id=uid,csrf='token')
    def post(self,data):return self.client.post('/my-applications/1/assessment',data={'csrf_token':'token',**data})
    def scalar(self,sql):
        con=sqlite3.connect(module.DB)
        try:return con.execute(sql).fetchone()[0]
        finally:con.close()
    def test_owner_and_order_validation(self):
        self.as_user(3);self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,404)
        self.as_user(1);self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,403)
        self.as_user(2)
        self.assertEqual(self.post({'step':2,'response':'Análise válida com evidências e justificativa suficiente.'}).status_code,400)
        self.assertEqual(self.post({'step':0,'response':'curto'}).status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM selection_assessments'),0)
    def test_full_flow_persists_and_does_not_score_training(self):
        response='Correlacionar identidade, origem e horário; preservar evidências e validar a hipótese antes de conter.'
        self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,200)
        for step in range(3):
            self.assertEqual(self.post({'step':step,'response':response}).status_code,302)
            self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,200)
        self.assertEqual(self.scalar('SELECT status FROM applications WHERE id=1'),'review')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM attempts'),0)
        before=self.scalar('SELECT content FROM selection_responses WHERE position=2')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM selection_responses'),3)
        self.assertEqual(self.post({'step':2,'response':'Tentativa de sobrescrever após envio final com outro texto.'}).status_code,302)
        self.assertEqual(self.scalar('SELECT content FROM selection_responses WHERE position=2'),before)
    def test_stage_cannot_be_overwritten(self):
        response='Relato com evidências suficientes e hipóteses justificadas.'
        self.post({'step':0,'response':response})
        self.assertEqual(self.post({'step':0,'response':response}).status_code,400)
    def test_legacy_assessment_migrates_to_relational_rows(self):
        import selection
        con=sqlite3.connect(os.path.join(self.temp.name,'legacy-selection.db'))
        try:
            con.execute("CREATE TABLE selection_assessments(application_id INTEGER PRIMARY KEY,scenario_json TEXT NOT NULL,responses_json TEXT NOT NULL,started_at INTEGER,updated_at INTEGER,submitted_at INTEGER)")
            con.execute('INSERT INTO selection_assessments VALUES(?,?,?,?,?,?)',(1,json.dumps([{'title':'Etapa original','briefing':'Briefing original'}]),json.dumps({'0':'Resposta original'}),1,2,2))
            selection.migrate(con);selection.migrate(con)
            self.assertEqual(con.execute('SELECT title,briefing FROM selection_stages').fetchall(),[('Etapa original','Briefing original')])
            self.assertEqual(con.execute('SELECT content FROM selection_responses').fetchall(),[('Resposta original',)])
        finally:con.close()

    def test_draft_is_not_eligible(self):
        con=sqlite3.connect(module.DB)
        try:con.execute("UPDATE applications SET status='draft' WHERE id=1");con.commit()
        finally:con.close()
        self.assertEqual(self.client.get('/my-applications/1/assessment').status_code,403)

if __name__=='__main__':unittest.main()
