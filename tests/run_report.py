"""Executa unittest e guarda evidências sem dados do banco real."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
records = []

class Result(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        records.append({'test':test.id(),'status':'APROVADO'})
    def addFailure(self, test, err):
        super().addFailure(test,err)
        records.append({'test':test.id(),'status':'FALHOU','detail':self._exc_info_to_string(err,test)})
    def addError(self, test, err):
        super().addError(test,err)
        records.append({'test':test.id(),'status':'ERRO','detail':self._exc_info_to_string(err,test)})
    def addSkip(self, test, reason):
        super().addSkip(test,reason)
        records.append({'test':test.id(),'status':'NAO EXECUTADO','detail':reason})

if __name__ == '__main__':
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    target=ROOT/'output/qa/unit-results.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    sys.exit(not result.wasSuccessful())
