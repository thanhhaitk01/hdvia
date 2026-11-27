import multiprocessing as mp, time, sys
sys.path.insert(0, '.')
TOPICS={
"DESTINATION":"Hội An có gì nổi bật?",
"HISTORY":"Lịch sử Hội An là gì?",
"CULTURE":"Văn hóa Hội An có gì đặc sắc?",
"FOOD":"Hội An có món gì đặc sản?",
"GUIDE_SCRIPT":"Thuyết minh Hội An cho khách thế nào?",
"WEATHER":"Thời tiết Hội An thế nào?",
"ROUTE":"Từ Hội An đi Huế mất bao lâu?",
"RISK":"Hội An có rủi ro gì cần lưu ý?",
"PLAN_B":"Nếu mưa ở Hội An thì Plan B thế nào?",
"TRANSPORT":"Giao thông ở Hội An thế nào?",
"PEOPLE":"Người dân Hội An có đặc điểm gì?",
"ECONOMY":"Kinh tế Hội An nổi bật ở đâu?",
}
N=1_000_000

def worker(item):
    topic,q=item
    from conversation_engine import ConversationIntelligenceEngine
    eng=ConversationIntelligenceEngine()
    ok=0; errors=0; wrong_intent=0; no_place=0
    expected={"DESTINATION":"DESTINATION","HISTORY":"HISTORY","CULTURE":"CULTURE","FOOD":"FOOD","GUIDE_SCRIPT":"GUIDE_SCRIPT","WEATHER":"WEATHER","ROUTE":"ROUTE","RISK":"RISK","PLAN_B":"PLAN_B","TRANSPORT":"TRANSPORT","PEOPLE":"PEOPLE","ECONOMY":"ECONOMY"}[topic]
    t=time.time()
    for i in range(N):
        r=eng.answer(f"{q} [QA-{i}]")
        ok+=1
        if r.get('intent') != expected: wrong_intent+=1
        if not r.get('places'): no_place+=1
    return topic,ok,wrong_intent,no_place,errors,time.time()-t

if __name__=='__main__':
    t=time.time()
    with mp.Pool(processes=min(len(TOPICS),mp.cpu_count())) as pool:
        rows=pool.map(worker, TOPICS.items())
    for row in sorted(rows): print(row)
    print('TOTAL_QUERIES',sum(r[1] for r in rows))
    print('TOTAL_SECONDS',round(time.time()-t,2))
