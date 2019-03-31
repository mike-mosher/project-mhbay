import requests
from bs4 import BeautifulSoup
import csv


# Globals
base_url = 'https://www.mhbay.com'
mhp_all_page = 'https://www.mhbay.com/mobile-home-park-directory/michigan/all'
excel_workbook_name = 'mhbay_mhp_michigan.csv'


def workbook_file_open(filename):
    """Open file and return object"""
    return open(filename, 'wt')


def workbook_open(workbook_file):
    """take open file and return CSV writer object"""
    return csv.writer(workbook_file)


def workbook_write_header(workbook, header):
    """Write header row to CSV writer object"""
    workbook.writerow(header)


def workbook_write_row(workbook, row):
    """Write row to CSV writer object"""
    workbook.writerow(row)


def workbook_close(workbook_file):
    """Close file"""
    workbook_file.close()


def get_total_parks_num():
    """
    Pull down website HTML and parse to find the total number of
    mobile home parks.
    String that we are looking for looks like this:
    "MHBay.com has 1,344 mobile home parks in Michigan."

    Returns:
        int -- number of mobile home parks (1344 as int)
    """

    # string I'm looking for: 'MHBay.com has x mobile home parks in Michigan'
    total_parks_string_prefix = 'MHBay.com has '
    total_parks_string_postfix = ' mobile home parks in Michigan'

    # Get html
    response = requests.get(mhp_all_page)

    # Remove all HTMl before total_parks_string_prefix
    response_left_index = response.text.find(
        total_parks_string_prefix) + len(total_parks_string_prefix)
    response_left_index_plus_rest_of_html = response.text[response_left_index:]

    # Remove all html after total_parks_string_postfix
    string_splice_right_index = \
        response_left_index_plus_rest_of_html.find(total_parks_string_postfix)
    num_mhp_total_num_str_w_commas = \
        response_left_index_plus_rest_of_html[:string_splice_right_index]

    # remove commas from html string and convert to integer
    num_mhp_total = int(num_mhp_total_num_str_w_commas.replace(',', ''))

    return num_mhp_total


def get_page(page_num):
    """Get html content of url as string"""

    url = f'{base_url}/mobile-home-park-directory/usa/page/{page_num}?state=MI&view=list'
    return requests.get(url).text


def html_to_soup(html):
    """Convert html string to BeautifulSoup object"""

    return BeautifulSoup(html, 'html.parser')


def parse_html_section_from_soup(soup):
    """Search for specific div in the BeautifulSoup object"""

    return soup.find('div', attrs={'class': 'item-listing list'})


def find_all_parks_in_soup(soup):
    """Return all items in BeautifulSoup object"""

    return soup.find_all('div', attrs={'class': 'item'})


def get_park_image(soup):
    """get image URL from BeautifulSoup object"""

    item_div = soup.find('div', attrs={'class': 'item-image'})
    image_link = item_div.find('img', attrs={'class': 'img-fluid'})['src']

    return image_link


def get_property_id(url):
    """Take URL and parse out Property ID"""

    # url = 'https://www.mhbay.com/mobile-home-parks/540377-hunters-crossing-in-capac-mi'

    # split creates: ['https:', 'www.mhbay.com', 'mobile-home-parks', '540377-hunters-crossing-in-capac-mi']
    url_path = url.split('/')[-1]   # return last item:  '540377-hunters-crossing-in-capac-mi'

    # url_path.split('-') creates: ['540377', 'hunters', 'crossing', 'in', 'capac', 'mi']
    property_id = url_path.split('-')[0]  # returns first item: '540377'

    return property_id


def get_park_info(soup):
    """Get park info div from BeautifulSoup object"""

    return soup.find('div', attrs={'class': 'item-info'})


def get_park_name(soup):
    """Get park name from BeautifulSoup object"""

    info = get_park_info(soup)
    park_title = info.find('h3', attrs={'class': 'item-title'})
    park_name = park_title.find('a').string

    return park_name


def get_park_page_link(soup):
    """Get park page link from BeautifulSoup object"""

    info = get_park_info(soup)
    park_title = info.find('h3', attrs={'class': 'item-title'})
    park_page_link = park_title.find('a')['href']

    return base_url + park_page_link


def get_park_address(soup):
    """
    Get park address items from BeautifulSoup object

    Arguments:
        soup {BeautifulSoup} -- BeautifulSoup object

    Returns:
        list -- list of address objects
    """

    location = soup.find('div', attrs={'class': 'item-location'})

    street_obj = location.find('span', attrs={'itemprop': 'streetAddress'})
    city_obj = location.find('span', attrs={'itemprop': 'addressLocality'})
    state_obj = location.find('span', attrs={'itemprop': 'addressRegion'})
    zipcode_obj = location.find('span', attrs={'itemprop': 'postalCode'})

    street = street_obj.string if street_obj else ''
    city = city_obj.string if city_obj else ''
    state = state_obj.string if state_obj else ''
    zipcode = zipcode_obj.string if zipcode_obj else ''

    return street, city, state, zipcode


def get_park_details(soup):
    """Get park details from BeautifulSoup object"""

    return soup.find('div', attrs={'class': 'item-details'}).string


def main():

    # Get total number of MHP parks in MHBay.com
    total_parks = get_total_parks_num()

    # Set page number range
    start_page_num = 1
    end_page_num = total_parks + 1
    num_pages = range(start_page_num, end_page_num)

    # Setup Excel Workbook
    workbook_file = workbook_file_open(excel_workbook_name)
    workbook = workbook_open(workbook_file)

    header = [
        'Park Property Id',
        'Park Name',
        'Park Street',
        'Park City',
        'Park State',
        'Park Zip',
        'Park Details',
        'Park Image Link',
        'Park Page Link'
    ]
    workbook_write_header(workbook, header)

    # screen scrape data
    for page_num in num_pages:
        page_html = get_page(page_num)
        soup = html_to_soup(page_html)
        relevent_html_section_as_soup = parse_html_section_from_soup(soup)
        list_of_parks_soup = \
            find_all_parks_in_soup(relevent_html_section_as_soup)

        for park in list_of_parks_soup:
            park_image_link = get_park_image(park)
            park_name = get_park_name(park)
            park_page_link = get_park_page_link(park)
            park_property_id = get_property_id(park_page_link)
            park_street, park_city, park_state, park_zip = \
                get_park_address(park)
            park_details = get_park_details(park)

            row = [
                park_property_id,
                park_name,
                park_street,
                park_city,
                park_state,
                park_zip,
                park_details,
                park_image_link,
                park_page_link
            ]

            workbook_write_row(workbook, row)

    # Close out excel sheet
    workbook_close(workbook_file)


if __name__ == "__main__":
    main()
