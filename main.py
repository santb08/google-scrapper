from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from playwright.sync_api import sync_playwright
import click
import base64
import io
import os
import requests
import re


INPUT_SELECTOR = 'input[name="q"]'
IMAGE_SELECTOR = '.rg_i'
GOOGLE_IMAGES_URL = 'https://images.google.com/'

READY_STATE = 'div[data-status="5"]'
LOADING_STATE = 'div[data-status="1"]'
END_OF_RESULTS_STATE = 'div[data-status="3"]'
result = []


def img_down(path, image_data):
  try:
    index = image_data['index']
    image_name = '-'.join(image_data['alt'].split(' ')[:5])
    image_name = f'{index}-{image_name}.jpeg'
    url = image_data['url']
    image = None

    if image_data['base64']:
      print('Base 64')
      # image = base64.urlsafe_b64decode(url)
      # image = Image.open(image)
      url = re.sub('^data:image/.+;base64,', '', url)
      print(url)
      image= Image.open(io.BytesIO(base64.urlsafe_b64decode(url)))

    else:
      # return
      response  = requests.get(url).content
      image_file = io.BytesIO(response)
      image  = Image.open(image_file)


    print('[Creating]', image_name)
    with open(f'{path}/{image_name}', "wb") as f:
      image.save(f , "JPEG")
      # print("Success!!!!")
  except Exception as e:
    print(e)


def scrap_images(query, limit):
  with sync_playwright() as pw:
    # create browser instance
    # we can choose either a Headful (With GUI) or Headless mode:
    browser = pw.chromium.launch(headless=False)

    # Create a new page and visit Google
    page = browser.new_page()
    page.goto(GOOGLE_IMAGES_URL)

    # Input search
    input = page.locator(INPUT_SELECTOR)
    input.type(query, delay=0)
    input.press('Enter')

    # Get all results from Google
    while not page.locator(END_OF_RESULTS_STATE).is_visible() and len(page.query_selector_all('.rg_i')) < limit:
      page.mouse.wheel(0, 600)

      load_more_results = page.locator('.r0zKGf')
      if load_more_results.is_visible():
        load_more_results.click()

      show_more_results = page.locator('input[type="button"]')
      if show_more_results.is_visible():
        show_more_results.click()

    images = page.query_selector_all('.rg_i')[0:limit]

    for index in range(len(images)):
      img = images[index]
      image_url = img.get_attribute('src') or img.get_attribute('data-src')

      image_data = {
        'alt': img.get_attribute('alt'),
        'url': image_url,
        'index': index,
        'base64': 'base64' in image_url[0:30]
      }

      result.append(image_data)

    return result


@click.command()
@click.option(
  '--output',
  help='Output folder.',
  required=True,
)
@click.option(
  '--query',
  prompt='Query to scrap from Google Images',
  help='The person to greet.',
)
@click.option(
  '--limit',
  help="The limit of images",
  default=50,
)
def main(output, query, limit):
  all_images = scrap_images(query, limit)

  if not os.path.exists(output):
   os.makedirs(output)
   print("Output folder not existing, created")

  path = os.path.abspath(output)
  print('[Downloading At]', path)

  with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(lambda x: img_down(path, x) , all_images)


if __name__ == '__main__':
  main()

print("All Images Downloaded Successfully")