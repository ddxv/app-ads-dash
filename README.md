# App-Ads-Dash: Exploratory Dash for Mobile app-ads.txt Insights

This is a free resource for anyone interested in mobile advertising data. Data is built from my open source project [AdsCrawler on Github](https://github.com/ddxv/adscrawler) and visualized by [App-Ads-Dash on Github](https://github.com/ddxv/app-ads-dash). A hosted version of the dash is publicly available at [ads.jamesoclaire.com](https://ads.jamesoclaire.com/dash/ads). Some blog articles about the data can also be [found on my blog](https://jamesoclaire.com).

[<img src="/static/bars_example.png" width="500"/>](/static/bars_example.png)

## Why

Advertising is the backbone of a free and open internet, but despite this is maligned. This means that the expectations for public data on advertising has begun to decline, but I believe that publicly available data for advertising is an important tool for fighting fraud, fighting monopolies and helping people make good decisions about the ways their apps/sites earn and spend advertising money.

The past decades have seen greater restrictions on freely accessing data and these projects are open source to help advertisers gain understanding to why having open access to data helps with verification and checking authenticity of advertising partners.

## Where to Access

A hosted version of the dash is publicly available at [ads.jamesoclaire.com](https://ads.jamesoclaire.com/dash/ads). Some blog articles about the data can also be [found on my blog](https://jamesoclaire.com).

## Self hosting:
### Setup

- If you want to run yourself, you will need the underlying data and database setup. To get that data you will need to run [AdsCrawler](https://github.com/ddxv/adscrawler).
- Pip install the requirements: `pip install -r requirements.txt`
- put config file in `~/.config/app-ads/config.yml` with server info like
```
  madrone: (any name, your server name)
    host: 12.34.56.78 (your ip)
    os_user: ubuntu (ssh login user)
    user: postgres (database user)
    password: xxxx (database user password)
    db: madrone (database name)
```
  
### Run
 - `python dashapp.py` to run locally
  


