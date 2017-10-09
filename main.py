import requests
from lxml import html
import sys

CONF_SEP = "::"

links_save_suffix = "_links"

base_url = "https://eksisozluk.com/basliklar/istatistik/{0}/son-entryleri?p={1}"
eksi_base_url = "https://eksisozluk.com"

def showusage():
    print("""
    Usage : python eksi_stalker.py <config-file>
    
    Config File Example
    =======================
    larker{0}71060300{0}larker_save.txt
    suser{0}12345678{0}file_name.txt
    
    """.format(CONF_SEP))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        showusage()
        sys.exit(1)

    config_file = sys.argv[1]
    susers = dict()

    with open(config_file, "r") as fConf:
        lines = list(map(lambda x : x[:-1] if x.endswith('\n') else x, fConf.readlines()))
        for line in lines:
            ln = line.split(CONF_SEP)
            susers[ln[0]] = {"last_stalked_entry_num" : ln[1], "save_file" : ln[2]}

    print("[i] Stalking process has been started.")
    for suser in susers:
        __continue_stalking = True

        print("[i] Stalking :", suser)
        print("  <*> Last stalked entry :", susers[suser]["last_stalked_entry_num"])

        _sf = susers[suser]["save_file"]
        suser_sf = open(_sf, "a")

        if "." in _sf:
            _suser_links_sf = _sf[:_sf.index(".")] + links_save_suffix + _sf[_sf.index("."):]
        else:
            _suser_links_sf = _sf + links_save_suffix + ".txt"

        suser_links_sf = open(_suser_links_sf, "a")

        print("  <*> Save file          :", _sf)
        print("  <*> Links save file    :", _suser_links_sf)

        pagenum = 1
        last_entry = 0

        while __continue_stalking:
            page = requests.get(base_url.format(suser, pagenum))

            if page.status_code != 200:
                print("[!] Status code is not 200")

                if page.status_code >= 400:
                    print("[ERROR] An error occured while trying to get page : '" + base_url.format(suser) + "'")
                    print("[*] Switching to next suser, passing", suser)
                    continue

            main_tree = html.fromstring(page.content.decode("utf-8"))
            lis = main_tree.xpath("//li/a[span]")

            if not len(lis):
                print("\n[i] End of entries. Switching to next suser.")
                continue
            else:
                print("\n[+]", len(lis), "entries found in page", pagenum)

            for entry in lis:
                entry_num = int(next(entry.iterchildren()).text[1:])
                if entry_num > int(susers[suser]["last_stalked_entry_num"]):
                    print("  => Saving entry", entry_num, "... ", end='')

                    entry_title = entry.text.replace("\r\n", "").strip()
                    entry_url = eksi_base_url + entry.values()[0]

                    entry_page = requests.get(entry_url)
                    if page.status_code != 200:
                        print("[!] Status code is not 200")

                        if page.status_code >= 400:
                            print("[ERROR] An error occured while trying to get page : '" + entry_url + "'")
                            print("[*] Switching to next entry, passing", entry_title, entry_num)
                            continue

                    entry_tree = html.fromstring(entry_page.content.decode("utf-8").replace("<br/>", "\n"))
                    #print("[DEBUG]", entry_url)
                    #entry_string = entry_tree.xpath("//li[@data-author]/div")[0].text.replace("\r\n", "")
                    entry_string = entry_tree.xpath("//li[@data-author]/div")[0].text_content().replace("\r\n", "").strip()

                    entry_links = list()
                    for lt in entry_tree.xpath("//li[@data-author]/div")[0].iterlinks():
                        if lt[1] == "href":
                            entry_links.append({"text" : lt[0].text,
                                                "href" : eksi_base_url + lt[2] if lt[2].startswith("/?q") or lt[2].startswith("/entry") else lt[2]})

                    suser_sf.write("[" + str(entry_num) + "] " + entry_title + "\n\n" + entry_string + "\n\n")

                    if len(entry_links):
                        suser_links_sf.write("[" + str(entry_num) + "] " + entry_title + "\n\n")
                        for ref in entry_links:
                            suser_links_sf.write(ref["text"] + " => " + ref["href"] + "\n")
                        suser_links_sf.write("\n")

                    print("DONE.")

                    if entry_num > last_entry:
                        last_entry = entry_num

                else:
                    print("\n[+] Entries of", suser, "is up to date now.")
                    __continue_stalking = False
                    break

            pagenum += 1

        suser_sf.close()
        suser_links_sf.close()

        lines = None
        with open(config_file, "r") as fSCon:
            _lines = fSCon.readlines()
            for line in _lines:
                if line.startswith(suser + CONF_SEP):
                    indx = _lines.index(line)
                    tmp = _lines[indx]
                    tmp = tmp.split(CONF_SEP)
                    tmp[1] = str(last_entry)
                    _lines[indx] = CONF_SEP.join(tmp)

                    lines = _lines
                    break

        if lines:
            with open(config_file, "w") as fSCon:
                fSCon.seek(0)
                fSCon.truncate()
                fSCon.writelines(lines)

        print("\n[+] Last stalked entry updated to", last_entry)

        print("[i] We're done with", suser, "!\n")

    print("[i] Stalking session finished.")
    sys.exit(0)