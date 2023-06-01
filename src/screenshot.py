from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from PIL import Image
from pyvirtualdisplay import Display

import time, string, random, os

temp_dir = r'tmp'
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
filebase = ''.join(random.choices(string.ascii_lowercase, k=10))
path_small_png = f'{temp_dir}/{filebase}_small.png'
path_large_png = f'{temp_dir}/{filebase}_large.png'

def wheel_element(element, deltaY = 120, offsetX = 0, offsetY = 0):
    error = element._parent.execute_script("""
      var element = arguments[0];
      var deltaY = arguments[1];
      var box = element.getBoundingClientRect();
      var clientX = box.left + (arguments[2] || box.width / 2);
      var clientY = box.top + (arguments[3] || box.height / 2);
      var target = element.ownerDocument.elementFromPoint(clientX, clientY);

      for (var e = target; e; e = e.parentElement) {
        if (e === element) {
          target.dispatchEvent(new MouseEvent('mouseover', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
          target.dispatchEvent(new MouseEvent('mousemove', {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY}));
          target.dispatchEvent(new WheelEvent('wheel',     {view: window, bubbles: true, cancelable: true, clientX: clientX, clientY: clientY, deltaY: deltaY}));
          return;
        }
      }
      return "Element is not interactable";
      """, element, deltaY, offsetX, offsetY)
    if error:
      raise WebDriverException(error)

def crop(image):
    im = Image.open(image)
    im_crop = im.crop((100, 270, 980, 1650))
    im_crop.save(image)

def delete_images(path_1, path_2):
    os.remove(path_1)
    os.remove(path_2)

def take_screenshoot(ref_catastral):
    display = Display(visible=0, size=(1080, 1920))
    display.start()
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')

    # Website URL to navigate
    url = 'https://idecyl.jcyl.es/vcig/?service=https://idecyl.jcyl.es/geoserver/lc/wms'

    # Navigate to the website
    driver.get(url)
    time.sleep(1)

    # close popup
    driver.find_element(By.CSS_SELECTOR, 'ion-icon.clicable.close-page.icon.icon-md.ion-md-close[role="img"][aria-label="close"]').click()
    time.sleep(1.5)

    # set satelite image
    driver.find_element(By.XPATH, '//*[@id="select-1-0"]/span').click()
    time.sleep(0.5)

    driver.find_element(By.XPATH, '/html/body/ion-app/ion-popover/div/div[2]/div/ng-component/ion-list/ion-item[2]/div[1]/ion-radio/button/span').click()
    time.sleep(1)

    # open side menu
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[1]/button/span/p').click()
    time.sleep(0.2)

    # open search menu
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[2]/div/a').click()
    time.sleep(0.2)

    # open catastro search
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[2]/div/div/app-searchs-segments/div/ion-segment/ion-segment-button[3]').click()
    time.sleep(0.2)

    # input catastro reference
    input_element = driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[2]/div/div/app-searchs-segments/div/div/app-catastro-search/ion-card/ion-card-content/form/div/ion-grid[1]/ion-row/ion-col/ion-item/div[1]/div/ion-input/input')
    input_element.send_keys(ref_catastral)
    input_element.send_keys(Keys.ENTER)
    time.sleep(4)

    # open capas menu
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[1]/div/a').click()
    time.sleep(0.2)

    # add parcelas layer
    input_element = driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[1]/div/div/app-toc-layers/app-group-layers/ion-item/div[1]/div/ion-input/input')
    input_element.send_keys('sigpac')
    time.sleep(0.2)

    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[1]/div/div/app-toc-layers/app-group-layers/div/div[10]/app-tree-container/ion-list/ion-list/ion-list/ion-item/div[1]/div/ion-label/app-group-layers/div/div[1]/app-tree-container/ion-list/ion-list/ion-list/ion-item/div[1]/div/ion-label/app-group-layers/div/div[2]/app-item-layer/div/ion-list-header/ion-icon').click()
    time.sleep(0.2)

    # close side menu
    elm = driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[1]/button/span').click()
    time.sleep(0.2)

    # zoom in
    elm = driver.find_element(By.XPATH, '//*[@id="ol-main-map"]/div/canvas')
    time.sleep(0.2)
    wheel_element(elm, -100)
    time.sleep(0.2)

    # first screenshot
    driver.save_screenshot(path_small_png)
    crop(path_small_png)

    # zoom out
    wheel_element(elm, 100)
    time.sleep(0.2)
    wheel_element(elm, 100)
    time.sleep(0.2)
    wheel_element(elm, 100)
    time.sleep(0.2)
    wheel_element(elm, 100)
    time.sleep(0.2)

    # open side menu
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[1]/button/span/p').click()
    time.sleep(0.2)

    # open capas menu
    driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[1]/div/a').click()
    time.sleep(0.2)

    # remove sigpac capa
    driver.find_element(By.XPATH, '/html/body/ion-app/ng-component/ion-nav/app-visor/app-side-multipanel/div[2]/app-side-multipanel-panel/div/app-map-tools/ul/li[1]/div/div/app-toc-layers/app-toc-layers-list/ion-list/ion-item-group/div/div[1]/app-layer-control-display/div/div[1]/ion-checkbox/button').click()
    time.sleep(0.2)

    # close side menu
    elm = driver.find_element(By.XPATH, '//*[@id="sideMultipanel"]/div[1]/button/span').click()
    time.sleep(0.2)

    # zoom out screenshot
    driver.save_screenshot(path_large_png)
    crop(path_large_png)

    # Close the browser
    driver.quit()

    return path_small_png, path_large_png
