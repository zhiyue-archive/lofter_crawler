# -*- coding: utf-8 -*-
__author__ = 'zhiyue'
from LofterLib import *


def CreateWorkListDic(PostHeader,MaxPage):
    url = 'http://wanimal.lofter.com/?page='
    Request = urllib2.Request(headers=PostHeader,url=url+'1')
    k       =  ''
    Times    =   0
    while   k==''   and Times<10:
        print   u'正在打开答案首页',url
        k   =   OpenUrl(Request).decode(encoding='utf-8',errors='ignore')#文本内容必须要经过编码，否则会导致搜索时出现故障
        if  k=='':
            print   u'第{}/10次尝试打开首页失败，1秒后再次打开'.format(Times+1)
            time.sleep(1)
        Times+=1

    if  k   ==  '':
        ErrorReturn(u'打开首页失败，请检查网络连接\n打开失败的网址为'+url)
    k   =   k.replace('\n','').replace('\r','')
    RequestDict =   {}
    LoopFlag =1
    for No  in  range(MaxPage):#从0开始，不要干从1开始这种反直觉的事
        RequestDict[No]    =   [urllib2.Request(url=url+str(No+1),headers=PostHeader),False]
    return RequestDict


#答案信息读取
def ThreadWorker(MaxThread=200,RequestDict={},Handle=""):#newCommitTag
    u"""
    *   功能
        *   将待打开的网页分配给每一个线程池迸发执行
        *   将解析所得的答案内容储存于数据库中
        *   主要函数
    *   输入
        *   数据库游标，用于储存答案内容
        *   最大线程数
        *   待打开网页Request字典
        *   标志符
            *   用于对不同类型的内容进行处理
            *   标志符来自CheckUpdate返回值
            *   话题的标志符为4
    *   返回
        *   无
    """
    MaxPage =   len(RequestDict)
    ReDict  =   returnReDict()
    html_parser=HTMLParser.HTMLParser()
    ThreadList=[]
    Times       =   0
    ErrorCount  =   0
    LoopFlag    =   True
    ImgList = []
    for Page in  range(MaxPage):
        ThreadList.append(threading.Thread(target=Handle,args=(ReDict,html_parser,RequestDict,Page,ImgList)))

    while   Times<10    and LoopFlag:
        print   u'开始第{}遍抓取，本轮共有{}张页面待抓取,共尝试10遍'.format(Times+1,len(ThreadList))
        Page    =   0
        while Page <  MaxPage:
            t   =   MaxThread - (threading.activeCount() - 1)
            if  t   >   0 :
                while  t   >   0  and Page < MaxPage :
                    ThreadList[Page].start()
                    Page += 1
                    t    -= 1
                time.sleep(0.1)
            else    :
                PrintInOneLine(u'正在读取页面，还有{}张页面等待读取'.format(MaxPage-Page))
                time.sleep(1)
        ThreadLiveDetect(ThreadList)

        LoopFlag    =   False
        MaxPage     =   0
        ThreadList  =   []
        for t   in  RequestDict:
            if  RequestDict[t][1]==False:
                ThreadList.append(threading.Thread(target=Handle,args=(ReDict,html_parser,RequestDict,t,ImgList)))
                MaxPage     +=  1
                LoopFlag    =   True
        Times   +=  1
        if  LoopFlag:
            print   u'第{}遍抓取执行完毕，{}张页面抓取失败,3秒后进行下一遍抓取'.format(Times+1,ErrorCount)
            time.sleep(3)
    return ImgList

def WorkForFetchUrl(ReDict={},html_parser=None,RequestDict={},Page=0,ImgDictList=[]):#抓取链接#注意，Page是字符串#Pass
    u"""
        *   功能
            *   抓取指定答案列表页面进行读取，分析处理得到答案Dict后添加至AnswerDictList中
            *   主要函数
        *   输入
            *   ReDict
                *   正则Map，直接传递给ReadAnswer
            *   html_parser
                *   html解析器，也是直接传递给ReadAnswer
            *   RequestDict
                *   待打开网页Map
            *   Page
                *   待打开页面，使用RequestDict[Page]获取页面Request头
            *   AnswerDictList
                *   答案列表，用于储存提取出的答案字典
            *   Flag
                *   标志符，针对不同的网页类型分别进行处理
        *   返回
             *   无
    """
    print   u"正在抓取第{}页上的链接".format(Page+1)
    AnswerList  =   []
    try :
        k   =   OpenUrl(RequestDict[Page][0]).decode(encoding='utf-8',errors='ignore')#文本内容必须要经过统一编码，否则字符串操作会出现各种未定义行为
    except  ValueError as  e:#对于40X错误不再继续读取
        print   e
        ErrorReportText(Info=u'读取页面内容出错\t:\t'+str(e))
        RequestDict[Page][1]=True
        return
    except  IOError as e    :#解压缩错误
        print   e
        return
    if  k=='':#网页未成功打开
        return

    Dict    =   ()
    text = k.replace('\r',"").replace('\n',"").decode(encoding="utf-8",errors='ignore')
    Dict    = ReDict['_page'].findall(text)

    for href in Dict:
        ImgDictList.append(href)
    print   u'第{}页抓取成功'.format(Page+1)
    if  RequestDict[Page][1]==False:#将答案链接列表储存于RequesDict中
        RequestDict[Page][1]=True

def WorkForFetchImgUrl(ReDict={},html_parser=None,RequestDict={},Page=0,ImgDictList=[]):#抓取图片链接#注意，Page是字符串#Pass
    u"""
        *   功能
            *   抓取指定答案列表页面进行读取，分析处理得到答案Dict后添加至AnswerDictList中
            *   主要函数
        *   输入
            *   ReDict
                *   正则Map，直接传递给ReadAnswer
            *   html_parser
                *   html解析器，也是直接传递给ReadAnswer
            *   RequestDict
                *   待打开网页Map
            *   Page
                *   待打开页面，使用RequestDict[Page]获取页面Request头
            *   AnswerDictList
                *   答案列表，用于储存提取出的答案字典
            *   Flag
                *   标志符，针对不同的网页类型分别进行处理
        *   返回
             *   无
    """
    print   u"正在抓取第{}页上的链接".format(Page+1)
    AnswerList  =   []
    try :
        k   =   OpenUrl(RequestDict[Page][0]).decode(encoding='utf-8',errors='ignore')#文本内容必须要经过统一编码，否则字符串操作会出现各种未定义行为
    except  ValueError as  e:#对于40X错误不再继续读取
        print   e
        ErrorReportText(Info=u'读取页面内容出错\t:\t'+str(e))
        RequestDict[Page][1]=True
        return
    except  IOError as e    :#解压缩错误
        print   e
        return
    if  k=='':#网页未成功打开
        return

    Dict    =   ()
    text = k.replace('\r',"").replace('\n',"").decode(encoding="utf-8",errors='ignore')
    Dict    = ReDict['_picture'].findall(text)

    for href in Dict:
        ImgDictList.append(href)
    print   u'第{}页抓取成功'.format(Page+1)
    if  RequestDict[Page][1]==False:#将答案链接列表储存于RequesDict中
        RequestDict[Page][1]=True
def getHeader():
    header ={
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        ,'Accept-Encoding':'gzip,deflate,sdch'
        ,'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6'
        ,'Connection' : 'keep-alive'
        ,'Cookie':'_ntes_nnid=b79158113b7d4e40e6f8a955cc9c311c,1400515755404; reglogin_hasopened=1; firstentry=%2Farchive.do%3FloftBlogName%3Dwanimal%26X-From-ISP%3D2|http%3A%2F%2Fwanimal.lofter.com%2F%3Fpage%3D1; usertrack=ezq0d1RoSZo/qHIeIGFDAg==; regtoken=2000; reglogin_isLoginFlag=; __utma=61349937.749894173.1390571639.1416120740.1416126615.30; __utmb=61349937.8.8.1416126670884; __utmc=61349937; __utmz=61349937.1415031948.24.14.utmcsr=zreading.cn|utmccn=(referral)|utmcmd=referral|utmcct=/archives/4604.html'
        ,'Host':'wanimal.lofter.com'
        ,'Referer':'http://wanimal.lofter.com/view'
        ,'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'
    }
    return  header
def LofterHelp():
    PostHeader = getHeader()
    RequestDic = CreateWorkListDic(PostHeader,45)
    PageList = ThreadWorker(20,RequestDict=RequestDic,Handle=WorkForFetchUrl)
    PageDict = {}
    NO = 0
    for p in PageList:
        PageDict[NO] = [p,False]
        NO +=1
    ImgList = ThreadWorker(20,RequestDict=PageDict,Handle=WorkForFetchImgUrl)
    DownLoadPicWithThread(ImgList=ImgList,MaxThread=40)

if __name__ == '__main__':
    try:
        LofterHelp()
    except Exception,e:
        print e
    else:
        print "Lofter Finish."
