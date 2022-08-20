import itertools
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
import time
from time import sleep, perf_counter
from threading import Thread

# True ---> book  :  False --->audio
Bool = True
prevlinks = []
categorylinks = []
site = "https://fidibo.com/books/search?key=اروین+یالوم"

def main(categorylink):
    count = 0
    pagelink = categorylink + "&page="
    totalScrapedInfo = []
    start_time = perf_counter()
    Th = []
    threads = []
    for page in range(1, 5):
        t = Thread(target=crawelpage, args=(page, pagelink, count, categorylink, totalScrapedInfo, Th))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    end_time = perf_counter()


    pd.set_option('display.max_rows', None, 'display.max_columns', None)
    df = pd.DataFrame(totalScrapedInfo)
    # Convert columns to best possible dtypes using dtypes supporting NA
    df.convert_dtypes()
    categoryname = categorylink.split("/")[4].split("?")[0]
    df.to_excel(f'a.xlsx', encoding="utf-8-sig", header=True, index=False)
    df.to_csv(f'a.csv', encoding="utf-8-sig", header=True, index=False)

    print(f'It took {end_time - start_time: 0.2f} second(s) to complete.')

    # TODO
    # if count == 0:
    #     break





def crawelpage(page, pagelink, count, categorylink, totalScrapedInfo, Th):
    while True:
        if page > 4:
            break
        if page % 10 == 0:
            time.sleep(10)
        try:
            driver = webdriver.Edge()
        except WebDriverException:
            driver = webdriver.Edge()

        if Bool:
            content = "&book_formats%5B%5D=text_book"
        else:
            content = "&book_formats%5B%5D=audio_book"

        try:
            driver.get(f"{pagelink}{page}")
        except WebDriverException:
            sleep(10)
            driver.get(f"{pagelink}{page}")


        try:
            if driver.find_element(By.XPATH, "/html/head/meta[5]").get_attribute("content") == "https://fidibo.com/":
                print("Done! 🤪🤍")
                Th.append(1)
                break
        except NoSuchElementException:
            driver.get(f"{pagelink}{page}")
            sleep(5)
            if driver.find_element(By.XPATH, "/html/head/meta[5]").get_attribute("content") == "https://fidibo.com/":
                print("Done! 🤪🤍")
                Th.append(1)
                break
        # try:
        #     driver.get(f"{pagelink}{page}")
        # except InvalidArgumentException:
        #     print(f"Exiting. Last page: {page}.")
        #     break
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        count = crawler(soup, count, Bool, totalScrapedInfo)
        print(f"page {page}  ----  Done")
        driver.quit()
        page += 4


def crawler(soup, count, Bool, totalScrapedInfo):
    driver = webdriver.Edge()
    alllinks = soup.select("div div div.item-of-list span.title-book a")
    links = soup.select("div div div.item-of-list")
    booleanbook = []
    booleanaudio = []

    for item in links:
        booleanaudio.append(item.select("div.item-image img.audio-file") != [])
        booleanbook.append(item.select("div.item-image img.audio-file") == [])
    booklinks = list(itertools.compress(alllinks, booleanbook))
    audiolinks = list(itertools.compress(alllinks, booleanaudio))
    error504 = False

    for anchor in booklinks:
        # TODO
        # if count == 0:
        # return 0
        try:
            driver.get('https://fidibo.com' + anchor.get('href'))
            if anchor.get('href') not in prevlinks:
                prevlinks.append(anchor.get('href'))
            else:
                break
        except WebDriverException:
            time.sleep(20)
            # driver.get('https://fidibo.com' + anchor.get('href'))
        try:
            infolist = driver.find_element(by=By.CSS_SELECTOR, value='.col-sm-11')
        except:
            print("---------------------------")
            print("  504 Gateway Timeout 🥺  ")
            error504 = True
            time.sleep(20)

        if error504:
            while error504:
                try:
                    driver.get('https://fidibo.com' + anchor.get('href'))
                    time.sleep(5)
                    infolist = driver.find_element(by=By.CSS_SELECTOR, value='.col-sm-11')
                    error504 = False
                    print("  504 Gateway Timeout Solved 🥳  ")
                    print("---------------------------")
                except NoSuchElementException:
                    time.sleep(10)
                    print("Page Down 🤬. ")

        informations = infolist.find_elements(by=By.CSS_SELECTOR, value="[class='author_title white']")
        author = informations[0].text.replace("نویسنده : ", "").replace("نویسنده :", "")
        if Bool == True:
            bookname = infolist.find_element(By.TAG_NAME, "strong").text.replace("کتاب ", "") \
                .replace("رمان ", "").replace("دانلود ", "").replace("صوتی ", "")
            for sign in ["|", "نوشته", f"{anchor}"]:
                if sign in bookname:
                    bookname = bookname.split(sign)[0]
        else:
            bookname = driver.find_element(By.XPATH, "//*[@id='content']/div[2]/article/div[1]/div/div["
                                                     "2]/div/div/div[1]/h1").text.replace("کتاب ", "") \
                .replace("رمان ", "").replace("دانلود ", "").replace("صوتی ", "").replace("پادکست ", "")
            for sign in ["|", "،", f"{author}نوشته ", "با صدای"]:
                if sign in bookname:
                    bookname = bookname.split(sign)[0]

        try:
            speaker = informations[2].text.replace("گوینده : ", "")
        except IndexError:
            speaker = np.nan
        try:
            translator = informations[1].text.replace("مترجم : ", "")
            if Bool == False:
                if "گوینده" in translator:
                    translator = np.nan
                    speaker = informations[1].text.replace("گوینده : ", "")
        except IndexError:
            translator = np.nan
        try:
            price = driver.find_element(By.CLASS_NAME, "book-price").get_attribute("innerHTML").replace(" تومان", "")
        except NoSuchElementException:
            price = np.nan
        slist = driver.find_element(By.CLASS_NAME, "book-tags")
        publication = slist.find_element(By.TAG_NAME, "a").text.replace("نشر ", "") \
            .replace("انتشارات ", "").replace("گروه انتشاراتی ", "")
        slist = slist.find_elements(By.TAG_NAME, "li")
        printprice = np.nan
        releaseedate = np.nan
        language = np.nan
        filesize = np.nan
        pages = np.nan
        ISBN = np.nan
        for li in slist:
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "قیمت نسخه چاپی":
                printprice = li.text.replace("قیمت نسخه چاپی", "").replace(" تومان", "")
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "تاریخ نشر":
                releaseedate = li.text
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "زبان":
                language = li.text
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "حجم فایل":
                filesize = li.text.replace(" مگابایت", "")
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "تعداد صفحات":
                pages = li.text.replace("صفحه", "")
            if li.find_element(By.TAG_NAME, "img").get_attribute("alt") == "شابک":
                ISBN = li.text

        try:
            description = driver.find_element(By.CLASS_NAME, "more-info").text
        except NoSuchElementException:
            description = np.nan
            # description = driver.find_element(By.CLASS_NAME, "more-info").text

        categories = driver.find_element(by=By.CSS_SELECTOR, value='.list-inline').text.replace("فیدیبو / ", "")
        categories = categories.split("/ ")
        categories.pop()
        if len(categories) == 0:
            categories = np.nan

        try:
            cover = driver.find_element(by=By.XPATH, value="//*[@id='book_img']").get_attribute('src')
        except NoSuchElementException:
            cover = np.nan

        scrapedinfobook = {
            "نام کتاب": bookname,
            "نویسنده": author,
            "مترجم": translator,
            "قیمت": price,
            "انتشارات": publication,
            "قیمت نسخه چاپی": printprice,
            "تاریخ انتشار": releaseedate,
            "زبان": language,
            "حجم فایل": filesize,
            "تعداد صفحات": pages,
            "شابک": ISBN,
            "توضیحات": description,
            "دسته بندی": categories,
            "آدرس کاور": cover,
        }

        scrapedinfoaudio = {
            "نام کتاب": bookname,
            "نویسنده": author,
            "مترجم": translator,
            "گوینده": speaker,
            "قیمت": price,
            "انتشارات": publication,
            "تاریخ انتشار": releaseedate,
            "زبان": language,
            "حجم فایل": filesize,
            "توضیحات": description,
            "دسته بندی": categories,
            "آدرس کاور": cover,
        }
        count += 1
        if Bool == True:
            totalScrapedInfo.append(scrapedinfobook)
            print(f"book number {abs(count)} Done 🥳")
            # print(prevlinks)
            # print(f"book number {abs(100 - count)} Done 😀")
        else:
            totalScrapedInfo.append(scrapedinfoaudio)
            print(f"audio number {abs(count)} Done 🥳")

    return count


if __name__ == "__main__":
    prevlinks = []
    baseUrl = "https://fidibo.com"
    driver = webdriver.Edge()
    driver.get(f"{baseUrl}")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = soup.select("ul.dropdown-menu  div.col-sm-12 li a")
    for link in links:
        linktext = (link.get("href"))
        if len(str(linktext).split("/")) == 3:
            section = linktext
            fullUrl = baseUrl + section
            categorylinks.append(fullUrl)
    driver.quit()
    # for categorylink in categorylinks[14:15]:
    #     main(categorylink)
    main(site)
