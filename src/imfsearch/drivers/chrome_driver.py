import chromedriver_autoinstaller
from selenium import webdriver
import os

chromedriver_autoinstaller.install()

opt = webdriver.ChromeOptions()
prefs = {
    'download.default_directory' : os.getcwd() + os.path.sep + "_docs",
    'directory_upgrade': True,
    'excludeSwitches': ['enable-logging']
}
opt.add_experimental_option("prefs", prefs)
opt.add_argument("--start-maximized")
opt.add_argument("--disable-gpu")

def install():
    chrome_drv = webdriver.Chrome(options=opt)
    return chrome_drv