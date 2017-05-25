import datetime
from threading import Timer
from zipfile import ZipFile
import xml.etree.ElementTree as ElementTree
import yagmail
import pickle
import re


password = "pass"
senderemail = "email"
# todo: replace the above login items with yagmail keychain feature

yag = yagmail.SMTP(senderemail, password)
wordsPP = 30000

initTime = datetime.datetime.utcnow()
timeOfDay = datetime.time(hour=6)
timeInterval = datetime.timedelta(days=1)

prevTime = initTime
nextTime = initTime + timeInterval
nextTime = nextTime.replace(hour=timeOfDay.hour,minute=timeOfDay.minute,second=timeOfDay.second,microsecond=timeOfDay.microsecond)

delta_t = nextTime-prevTime
secs = delta_t.seconds+1

def XHTMLtoYagmail (input, namesp, css, disablehyperlinks = False):
    x = input.split("<html:")
    y = ""
    for each in x:
        y += each
        y += "<"
    y = y[:-1]

    x = y.split("</html:")
    y = ""
    for each in x:
        y += each
        y += "</"
    y = y[:-2]

    if namesp != "":
        x = y.split(" xmlns:html=\"" + namesp[1:-1] + "\"")
        y = ""
        for each in x:
            y += each

    if css != "":
        clean = css.replace("\n", " ")
        css = clean
        clean = css.replace("\t", " ")
        clean = "<head> <style> " + clean + " </style> </head> "
        #y = "<head> <style> .indent {   text-indent: 30em; } </style> </head>" + y
        y = clean + y

    if disablehyperlinks == True:
        y = re.sub("href=\".*\"", "", y)
    return y

inputpath = 'Nietzsche.epub'

class eBook:
    name = ""
    path = ""

    progress = 0
    totalWords = 0

    navMap = 0
    navPoints = {}
    contentItems = {}
    metadata = {}

    manifestItems = {}
    spineItems = []
    
    def __init__(self, path, name = ""):
       self.name = name


booklibrary = {}



def parse_and_get_ns(file):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ElementTree.iterparse(file, events):
        if event == "start-ns":
            if elem[0] in ns and ns[elem[0]] != elem[1]:
                # NOTE: It is perfectly valid to have the same prefix refer
                #     to different URI namespaces in different parts of the
                #     document. This exception serves as a reminder that this
                #     solution is not robust.    Use at your own peril.
                raise KeyError("Duplicate prefix with different URI found.")
            ns[elem[0]] = "{%s}" % elem[1]
        elif event == "start":
            if root is None:
                root = elem
    return ElementTree.ElementTree(root), ns

with ZipFile(inputpath) as book:
    TOC, TOCnamespace = parse_and_get_ns(book.open([s for s in book.namelist() if ".ncx" in s][0]))#ElementTree.parse(book.open([s for s in book.namelist() if ".ncx" in s][0]))
    contents, CONTnamespace = parse_and_get_ns(book.open([s for s in book.namelist() if ".opf" in s][0])) #ElementTree.parse(book.open([s for s in book.namelist() if ".opf" in s][0]))

    booklibrary[inputpath] = eBook(inputpath)
    #booklibrary[inputpath].metadata = contents.getroot().find(CONTnamespace[""] + "metadata")
    for each in list(contents.getroot().find(CONTnamespace[""] + "metadata")):
        booklibrary[inputpath].metadata[each.tag[each.tag.find('}')+1:]] = each.text
    booklibrary[inputpath].name = booklibrary[inputpath].metadata["title"]

    booklibrary[inputpath].navmap = TOC.getroot().find(TOCnamespace[""] + 'navMap')

    for item in booklibrary[inputpath].navmap:
        linkname = item.find(TOCnamespace[""] + 'navLabel').find(TOCnamespace[""] + 'text').text
        link = item.find(TOCnamespace[""] + 'content').attrib['src']
        booklibrary[inputpath].navPoints[linkname] = link

    for item in contents.getroot().find(CONTnamespace[""] + 'manifest'):
        booklibrary[inputpath].manifestItems[item.attrib['id']] = item.attrib['href']
    for item in contents.getroot().find(CONTnamespace[""] + 'spine'):
        booklibrary[inputpath].spineItems.append(booklibrary[inputpath].manifestItems[item.attrib['idref']])
        #booklibrary[inputpath].spineItems[item.attrib['idref']] = manifestItems[item.attrib['idref']]

    file = (book.open(booklibrary[inputpath].spineItems[16]))
    #file = ElementTree.fromstring(book.read(booklibrary[inputpath].spineItems[16]).decode("utf-8"))
    namespace = file.tag[0:file.tag.find('}')+1]
    section = file.find(namespace + 'body')
    total = sum(len(text.split()) for text in section.itertext())

    #print sample text in order to decide which file is the start of the actual book
    samplecount = 0
    for child in section[:5]:
        for text in child.itertext():
            if (samplecount + len(text.split(" "))) <= 100:
                samplecount += len(text.split(" "))
                print(text)

    css = ""
    for id in booklibrary[inputpath].manifestItems:
        if "css" in booklibrary[inputpath].manifestItems[id]:
            css += book.read(booklibrary[inputpath].manifestItems[id]).decode("utf-8")


    count = 0
    pagetext = ''
    position = 0
    headerfound = False

    

    for child in section:
        total2 = sum(len(text.split(" ")) for text in child.itertext())
        #print(total2)
        #print(" ".join(child.itertext()).split(" "))
        """"#print(len(" ".join(child.itertext()).split(" ")))
        #print(section[position])
        #print(child.tag)
        if (child.tag == namespace + "h1") or (child.tag == namespace + "h2") or (child.tag == namespace + "h3") or (child.tag == namespace + "h4") or (child.tag == namespace + "h5") or (child.tag == namespace + "h6"):
            if count + sum(len(text.split()) for text in section[position+1].itertext()) <= wordsPP:
                count += total2
                pagetext += ElementTree.tostring(child, "unicode")
                headerfound = True
        elif (count + total2 <= wordsPP):
            count += total2
            pagetext += ElementTree.tostring(child, "unicode")
            if headerfound == True:
                headerfound = False
        elif headerfound == True:
            headerfound = False
            count += total2
            pagetext += ElementTree.tostring(child, "unicode")
        else:
            #print(XHTMLtoYagmail(pagetext, namespace, css, True) + "\n\n")
            #yag.send(senderemail, "", XHTMLtoYagmail(pagetext, namespace, css, True))
            pagetext = ElementTree.tostring(child, "unicode")
            count = 0
        position += 1
    position = 1

    if count != 0:
        #print(XHTMLtoYagmail(pagetext, namespace, css, True) + "\n\n")
        #yag.send(senderemail, "", XHTMLtoYagmail(pagetext, namespace, css, True))
        pagetext = ElementTree.tostring(child, "unicode")
        count = 0

        #print(str(total2))
    #print(ElementTree.tostring(section, encoding='unicode', method='text'))
    #yag.send(senderemail, "", book.read(booklibrary[inputpath].spineItems[16]).decode("utf-8"))
    """


