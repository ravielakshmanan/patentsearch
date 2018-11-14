# U.S. patent scraper

A Python CLI utility to fetch data on patents recently awarded to inventors in `{{ your city }}`.

### Prereqs
* `python`
* `virtualenv`/`virtualenvwrapper`

### Setup
Clone this repo, then:
```
$ mkvirtualenv patents
$ pip install -r requirements.txt
$ python patent_scraper.py [args]
```

### Arguments
* `--city`: city, defaults to "Austin"
* `--state`: two-letter state abbreviation, defaults to "TX"
* `--days`: how many days back to search, defaults to 7

### Example usage
`python patent_scraper.py --city shelton --state wa`

If the city has more than one word, enclose it in quotes:
`python patent_scraper.py --city "new york" --state ny`

### Output
If you get any hits, you'll see two new files in your working directory:

1. `links_to_recent_patents.txt`: A newline-separated list of links returned by your search. Saving locally means you won't hammer the government servers needlessly.
2. `recent_patents.json`: A JSON file with an array of objects that look like this:

Key | Value description | Type
----|-------------|------
`url` | Link to the patent detail page | `string`
`description` | Brief description of the patent | `string`
`assignee` | Name of the patent assignee, often a company | `string`
`award_date` | Human-readable date of the award | `string`
`link_to_pdf` | Link to a PDF of the patent award hosted in a PTO document reader | `string`
`inventors` | Array of objects containing the inventors' names ("last" and "rest"), cities and states | `array`

### References
* [U.S. PTO Advanced Search](http://patft.uspto.gov/netahtml/PTO/search-adv.htm)
* [Class-based scraping with the NPR apps crew](http://blog.apps.npr.org/2016/06/17/scraping-tips.html)
