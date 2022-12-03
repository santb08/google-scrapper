from playwright.sync_api import sync_playwright
import requests
import io
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


INPUT_SELECTOR = 'input[name="q"]'
IMAGE_SELECTOR = '.rg_i'
GOOGLE_IMAGES_URL = 'https://images.google.com/'

READY_STATE = 'div[data-status="5"]'
LOADING_STATE = 'div[data-status="1"]'
END_OF_RESULTS_STATE = 'div[data-status="3"]'
result = []

def write_images(images):
  file = open('./results.txt', 'w')
  for image in images:
    file.write(image + '\n')

def img_down(link):
  response  = requests.get(link).content
  image_file = io.BytesIO(response)
  image  = Image.open(image_file)
  with open(link.split('/')[-1] , "wb") as f:
    image.save(f , "JPEG")
    # print("Success!!!!")

def scrap_ijjmages():
  with sync_playwright() as pw:
    # create browser instance
    # we can choose either a Headful (With GUI) or Headless mode:
    browser = pw.chromium.launch(headless=False)

    # Create a new page and visit Google
    page = browser.new_page()
    page.goto(GOOGLE_IMAGES_URL)

    # Input search
    input = page.locator(INPUT_SELECTOR)
    input.type('Sea', delay=0)
    input.press('Enter')

    # Get all results from Google
    while not page.locator(END_OF_RESULTS_STATE).is_visible():
      page.mouse.wheel(0, 400)

      load_more_results = page.locator('.r0zKGf')
      if load_more_results.is_visible():
        load_more_results.click()

      show_more_results = page.locator('input[type="button"]')
      if show_more_results.is_visible():
        show_more_results.click()

    images = page.query_selector_all('.rg_i')

    for img in images:
      image_url = img.get_attribute('src') or img.get_attribute('data-src')
      result.append(image_url)

    return result

write_images(result)

if __name__ == '__main__':
  all_images = scrap_images()
  with ThreadPoolExecutor(max_workers=10) as executor:
      executor.map(img_down , all_images)
  print("All Images Downloaded Successfully")