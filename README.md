# Stock Market Trading Simulator

[![made-with-flask](https://img.shields.io/static/v1?label=Made%20with&message=Flask&color=informational&style=flat&logo=Flask)](https://palletsprojects.com/p/flask/)
[![maintainer](https://img.shields.io/static/v1?label=Maintainer&message=nishant-nayak&color=green&style=flat&logo=Github)](https://github.com/nishant-nayak)
[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)
---

## Features

- Users can login and register through the web interface
![login-img](/assets/img/login.jpg)

- Users can view their current portfolio
![portfolio-img](/assets/img/portfolio.jpg)

- Users can buy and sell shares using virtual cash
![sell-img](/assets/img/sell.jpg)

- Users can view their detailed transaction history
![history-img](/assets/img/history.jpg)

- Latest share prices obtained from the [IEX Cloud](https://iexcloud.io/) API

## How to Install

1. Clone the repository using the following command:<br>
`git clone https://github.com/nishant-nayak/finance-flask.git`

2. Install all the necessary Python package requirements by running the following command:<br>
`pip install -r requirements.txt`

3. Set up the [Environment Variables](#environment-variables)

4. To run the Flask server on localhost port 5000, run the following command:<br>
`flask run`

## Environment Variables

The API_KEY is stored in a `.env` file within the project folder. To obtain an API Key, follow the steps defined at [IEX Cloud](https://iexcloud.io/core-data/). For the project to work, create a file with the name `.env` and enter the following contents:<br>
`API_KEY=<Your-API-Key-Here>`

## Contact

[GitHub](https://github.com/nishant-nayak) | [Email](mailto:nishantnayak2001@gmail.com) | [LinkedIn](https://www.linkedin.com/in/nishant-nayak-01/)
