import unittest
from entity_resolution import EntityResolver

class TravelAdapter:
    DATA={
        "chua cau":("Q1091054","Japanese Bridge","Japanese Bridge, Hoi An, Vietnam"),
        "japanese bridge":("Q1091054","Japanese Bridge","Japanese Bridge, Hoi An, Vietnam"),
        "thanh dia my son":("Q132951","My Son Sanctuary","My Son Sanctuary, Vietnam"),
        "my son sanctuary":("Q132951","My Son Sanctuary","My Son Sanctuary, Vietnam"),
        "ba na hills":("Q810815","Ba Na Hills","Ba Na Hills, Da Nang, Vietnam"),
    }
    def wikidata(self, query, limit=5):
        row=self.DATA.get(str(query).lower())
        if not row: return {"ok":True,"data":{"search":[]}}
        q,l,d=row
        return {"ok":True,"data":{"search":[{"id":q,"label":l,"description":d}]}}

class TestRealWorldQA(unittest.TestCase):
    def test_real_world_landmark_queries(self):
        resolver=EntityResolver(TravelAdapter())
        cases=[
            ("Chùa Cầu","Q1091054"),("Chùa Cầu Hội An","Q1091054"),
            ("Cầu Nhật Bản Hội An","Q1091054"),("Japanese Bridge","Q1091054"),
            ("Thánh địa Mỹ Sơn","Q132951"),("Thánh địa Mỹ Sơn Hội An","Q132951"),
            ("Ba Na Hills","Q810815"),("Ba Na Hill","Q810815"),
        ]
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(resolver.resolve(query)["wikidata"]["id"], expected)

    def test_unknown_query_fails_closed(self):
        r=EntityResolver(TravelAdapter()).resolve("Một địa danh hoàn toàn không có")
        self.assertEqual(r["confidence"], "UNRESOLVED")
        self.assertIsNone(r["wikidata"])

if __name__ == "__main__": unittest.main()
