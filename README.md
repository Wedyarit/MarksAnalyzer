# MarksAnalyzer

The analyzer is designed to analyze the user's current assessments, calculate all the necessary parameters.


# Features

- Simple use
- Automatic collection of data from the [school website](http://best.yos.kz/cabinet/)
- Calculating the number of ratings
- Calculating the average score for each subject
- Calculation of the number of receiving 9 points before achieving the "Excellent" status
- Calculation of the average score in all subjects
- Greate appearence

> Why do boring math when you can get others to do it for you?

This is exactly what I thought when developing this program.

# Usage
1. Clone the repository to your local environment
2. Set the required parameters in the configuration file
3. Run the program
4. Enjoy!

# Installation

There are several modules required for the program to work correctly.
Install the dependencies and devDependencies and start the usage.

```sh
$ pip install mechanicalsoup
$ pip install prettytable
$ pip install bs4
```
# Options
```py
class Options:
	LOGIN = 'your_login'
	PASSWORD = 'your_password'

	EXCELLENT_MARK = 8
	MAX_MARK = 10
```

The config file consists of several lines.
- Login - your login from the [site](http://best.yos.kz/cabinet/)'s account
- Password - your password from the [site](http://best.yos.kz/cabinet/)'s account
- Excellent mark - the value of the grade taken as "excellent"
- Maximum mark - the maximum possible score to obtain

You can read the configuration file [here](options.py).

# Appearance
This is one example of how the final result of the program will look like.
![](https://i.imgur.com/QnO7ZOI.png)

If the password or login was specified incorrectly, the program will display a corresponding message.
![](https://i.imgur.com/ESLaH27.png)

## Contributing
The works were done and decorated by [@Wedyarit (Vyacheslav)](https://github.com/Wedyarit).

## Feedback
Telegram: [@Wedyarit](https://t.me/Wedyarit)

