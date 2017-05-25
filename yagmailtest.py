import yagmail

password = "gaF6Suoglu\'k"
senderemail = "pe6eki@gmail.com"
yag = yagmail.SMTP(senderemail, password)

f = open("test.html")

def XHTMLtoYagmail (input = "", namesp = ""):
    x = input.split("<html:")
    y = ""
    for each in x:
        y += each
        y += "<"

    y = y[:-1]

    if namesp != "":
        temp = " xmlns:html=\"" + namesp[1:-1] + "\""
        x = y.split(temp)
        y = ""
        for each in x:
            y += each
    return y

#yag.send(senderemail, "", "<h3 xmlns:html=\"http://www.w3.org/1999/xhtml\" class=\"h3b\" id=\"p001_c001\"><a id=\"page_9\" /><strong class=\"calibre6\">ZARATHUSTRA’S PROLOGUE<br class=\"calibre2\" />I</strong></h3>")
input = "<html:h3 xmlns:html=\"http://www.w3.org/1999/xhtml\" class=\"h3b\" id=\"p001_c001\"><html:a id=\"page_9\" /><html:strong class=\"calibre6\">ZARATHUSTRA’S PROLOGUE<html:br class=\"calibre2\" />I</html:strong></html:h3>"

print(XHTMLtoYagmail(input, "{http://www.w3.org/1999/xhtml}"))
