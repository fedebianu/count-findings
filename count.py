import config
from count_core import CountCore

def main():
    analyzer = CountCore(
        token=config.TOKEN,
        sr=config.SR,
        domains=config.DOMAINS
    )
    analyzer.analyze()

if __name__ == '__main__':
    main()