import multiprocessing as mp, time, sys
sys.path.insert(0, '.')
TOPICS={
"DESTINATION":"Hội An có gì nổi bật?","HISTORY":"Lịch sử Hội An là gì?","CULTURE":"Văn hóa Hội An có gì đặc sắc?","FOOD":"Hội An có món gì đặc sản?","GUIDE_SCRIPT":"Thuyết minh Hội An cho khách thế nào?","WEATHER":"Thời tiết Hội An thế nào?","ROUTE":"Từ Hội An đi Huế mất bao lâu?","RISK":"Hội An có rủi ro gì cần lưu ý?","PLAN_B":"Nếu mưa ở Hội An thì Plan B thế nào?","TRANSPORT":"Giao thông ở Hội An thế nào?","PEOPLE":"Người dân Hội An có đặc điểm gì?","ECONOMY":"Kinh tế Hội An nổi bật ở đâu?"}
N=1_000_000
EXPECTED={k:k for k in TOPICS}
def worker(item):
    topic,q=item
    from conversation_engine import ConversationIntelligenceEngine
    eng=ConversationIntelligenceEngine(); wrong=0; no_place=0
    t=time.time()
    for i in range(N):
        intents=eng.detect_intents(f"{q} [QA-{i}]")
        places=eng.resolve_places(f"{q} [QA-{i}]")
        if EXPECTED[topic] not in intents: wrong+=1
        if not places: no_place+=1
    return topic,N,wrong,no_place,round(time.time()-t,2)
if __name__=='__main__':
    t=time.time()
    with mp.Pool(processes=4) as pool:
        rows=pool.map(worker, TOPICS.items())
    for r in sorted(rows): print(r)
    print('TOTAL_LIGHT_QUERIES',sum(r[1] for r in rows)); print('SECONDS',round(time.time()-t,2))
