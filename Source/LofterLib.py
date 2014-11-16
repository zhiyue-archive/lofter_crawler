# -*- coding: utf-8 -*-
#公共库
import  sys#修改默认编码#放置于首位
reload( sys )
sys.setdefaultencoding('utf-8')

import  sqlite3#使用数据库管理数据

import  pickle


import  urllib2
import  urllib#编码请求字串，用于处理验证码
import  socket#用于捕获超时错误
import  zlib
import  threading
import  re
import  HTMLParser#HTML解码&lt;
import  json#在returnPostHeader中解析Post返回值


import  time
import  datetime
import md5
import  os#打开更新页面
####
#工具程序所用模块
import  ConfigParser#ini文件读取，Setting()
import  shutil#文件操作模块
#用于存放工具性函数



def OpenUrl(Request,TimeOut=5):#打开网页，只尝试1次，失败时返回空字符串，错误信息中包含未打开网址。
    u"""
        *   功能
            *   打开Request中指定的网页，成功则返回原始网页内容\
                (只针对gzip进行解压缩，对其他格式例如jpg直接返回二进制内容，不进行额外处理)
            *   只尝试一次，失败返回空字符串
        *   输入
            *   Request
                *   待打开的Http请求
            *   TimeOut
                *   超时时间
        *   返回
            *   所打开网页的原始内容
            *   失败返回空字符串
    """
    try:
        Content = urllib2.urlopen(Request,timeout=TimeOut)
    except  urllib2.HTTPError   as  inst:
        print inst
        if int(inst.code/100)   ==  4:
            print   u'404错误'
            raise   ValueError(u"404 Not Found"+u"错误页面\t: \t"+Request.get_full_url())
        else:
            if  int(inst.code/100)  ==  5:
                print   u'服务器繁忙ing，稍后重试'
            else:
                print inst.code
                print u'打开网页出现未知错误'
    except  urllib2.URLError    as  inst    :
        print inst
        print inst.reason
        print u'错误网址：' + Request.get_full_url()
        print u'打开网页异常#稍后重试'
    except  socket.timeout as e:
        print   e
        print   u'打开网页超时'
    else:
        if Content.info().get(u"Content-Encoding")=="gzip":
            try:
                k = zlib.decompress(Content.read(),16+zlib.MAX_WBITS)
            except zlib.error as ziperror:
                print u'解压缩出错'
                print u'错误信息： '
                print ziperror
                raise   IOError(u"解压网页内容时出现错误"+u"错误页面\t: \t"+Request.get_full_url)
        else:
            k = Content.read()
        return  k
    return ''


def CheckImgFileExist(CheckList=[],ErrorList=[]):
    u"""
        *   功能
            *   检测CheckList中的文件是否存在，将不存在的文件添加到ErrorList中
        *   输入
            *   CheckList
            *   ErrorList
        *   返回
            *   无
    """
    for url in  CheckList:
        MetaName = u'../lofter/'   +   CalMd5Name(url)
        if not os.path.isfile(MetaName):
            ErrorList.append(url)
def ThreadLiveDetect(ThreadList=[]):
    u"""
        *   功能
            *   等待给定list中的线程执行完毕
        *   输入
            *   线程列表
        *   返回
            *   待列表中的所有线程执行完毕后返回
            *   不会检测死锁
    """
    liveFlag = True
    while liveFlag:
        liveFlag = False
        Running = 0
        for t in ThreadList:
            if t.isAlive():
                liveFlag = True
                Running +=1
        PrintInOneLine( u"目前还有{}条线程正在运行，等待所有线程执行完毕".format(Running))
        time.sleep(1)
def DownLoadPicWithThread(ImgList=[],MaxThread=20):
    u"""
        *   功能
            *   下载ImgList中的所有图片
            *   若图片下载失败，将图片地址打印并输出至[未成功下载的图片.txt]中
        *   输入
            *   ImgList
                *   待下载图片列表
            *   MaxThread
                *   最大线程数
        *   返回
            *   无
    """
    Time=0
    MaxPage = len(ImgList)
    ErrorList = []
    while Time<10 and MaxPage>0:
        Buf_ImgList = []
        Time+=1
        ThreadList = []
        buf_t_PageRecord = 0
        for t in ImgList:
            buf_t_PageRecord += 1
            ThreadList.append(threading.Thread(target=DownloadImg,args=(t,Buf_ImgList,u"{}/{}".format(buf_t_PageRecord,MaxPage))))
        Page = 0
        while Page < MaxPage:
            t = MaxThread - (threading.active_count()-1)
            if t > 0 :
                while t > 0 and Page < MaxPage :
                    ThreadList[Page].start()
                    Page += 1
                    t -=1
                time.sleep(0.1)
            else    :
                PrintInOneLine(u'第({}/10)轮下载图片，还有{}张图片等待下载'.format(Time,MaxPage-Page))
                time.sleep(1)
        ThreadLiveDetect(ThreadList)

        ImgList =   list(set(ImgList)-set(Buf_ImgList))
        ErrorList += Buf_ImgList
        Buf_ImgList = []
        CheckImgFileExist(CheckList=ImgList,ErrorList=Buf_ImgList)
        ImgList = Buf_ImgList
        MaxPage = len(ImgList)
        if  MaxPage!=0:
            print u'第{}轮下载执行完毕，剩余{}张图片等待下载'.format(Time,MaxPage)
            time.sleep(1)
        else    :
            print u'\n所有图片下载完毕'
    ErrorList = list(set(ErrorList))
    if len(ErrorList)>0:
        print u'开始输出下载失败的图片列表'
        f = open(u'../下载失败的图片列表.txt','a')
        f.write(u'\n---------------------------------------\n')
        f.write(u'时间戳:\t'+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())+'\n')
        f.write(u'\n---------------------------------------\n')
        print u'以下文件下载失败'
        for t in ErrorList:
            f.write(t+'\n')
            print t
        f.close()
def DownloadImg(imghref='',ErrorList=[],successprint=""):
    u"""
        *   功能
        *   下载图片，将下载失败的图片存入ErrorList中
        *   会先检测图片池中有没有对应的图片
            *   若无，下载图片
        *   输入
            *   imghref
                *   图片地址
            *   ErrorList
                *   下载失败时将链接存入此处
        *   返回
            *   无
    """
    try:
        CheckName = u'../Lofter/'
        try:
            MetaName = CalMd5Name(imghref)
        except  AttributeError:
            raise ValueError(u'程序出现错误，未能成功提取出下载地址'+u'目标网址'+imghref)
        if not os.path.isfile(CheckName+MetaName):
            k = OpenUrl(urllib2.Request(imghref),TimeOut=10)#这里会返回IOError
            if len(k)==0:
                print u"Download Image "+MetaName+"error,will try again soon"
                return 0
            imgfile = open(CheckName+MetaName,"wb")
            imgfile.write(k)
            imgfile.close()
    except  ValueError as e :
        print e
        ErrorList.append(imghref)
        PrintInOneLine(u'图片{}下载失败\r'.format(MetaName))
        ErrorReportText(u'图片下载错误\t:\t'+str(e))
    except  IOError as  e   :
        print e
        ErrorList.append(imghref)
        PrintInOneLine(u'图片{}下载失败\r'.format(MetaName))
        ErrorReportText(u'图片下载错误\t:\t'+str(e))
    else    :
        PrintInOneLine( u'图片{}下载成功\r'.format(MetaName)+successprint)


def PixName(url):#PassTag
    return re.search(r'[^/"]*?\.jpg',url).group(0)
def CalMd5Name(url):
    m = md5.new()
    m.update(url)
    return m.hexdigest()+'.jpg'
def PrintInOneLine(text=''):#Pass
    u"""
        *   功能
            *   反复在一行内输出内容
            *   输出前会先将光标移至行首，输出完毕后不换行
        *   输入
            *   待输出字符
        *   返回
            *   无
            *   若输出失败则将失败的文本输出至[未成功打开的页面。txt]内
    """
    try:
        sys.stdout.write("\r"+" "*60+'\t')
        sys.stdout.flush()
        sys.stdout.write(text)
        sys.stdout.flush()
    except:
        ErrorReportText(text)


def ErrorReportText(Info='',flag=True):
    u"""
        *   功能
            *   将错误信息写入到[ErrorReport.txt]中
        *   输入
            *   Info
                *   错误信息
            *   flag
                *   标识符
                *   True    ->  新建文件
                *   False   ->  在原有的文件上添加
        *   返回
            *   无
    """
    if flag :
        f = open(u'ErrorReport.txt','ab')
    else    :
        f = open(u'ErrorReport.txt','wb')
    f.write(Info)
    f.close()


def returnReDict():#返回编译好的正则字典#Pass
    u"""
        *   功能
            *   返回编译完成的正则表达式字典
        *   输入
            *   无
        *   返回
             *   无
    """
    Dict    =   {}
    Dict['_page']   =   re.compile(r'(?<=<div class="imgwrapper"><a href=").*?(?=">)')
    Dict['_picture']    =   re.compile(r'(?<=bigimgsrc=").*?(?=">)')
    return Dict

def ErrorReturn(ErrorInfo=""):#返回错误信息并退出，错误信息要用unicode编码
    u"""
        *   功能
            *   打印错误信息，等待用户敲回车之后再退出
        *   输入
            *   ErrorInfo
                *   待打印错误信息
        *   返回
            *   无
     """
    print   ErrorInfo
    print   u"点按回车退出"
    raw_input()
    os._exit(0)