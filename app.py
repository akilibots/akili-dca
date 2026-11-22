"""Scheduled accumulation on dYdX Chain, with durable order IDs."""
import time

from exchange import Exchange, TERMINAL
from runtime import State, load_config, log, number, single_instance


class DCA:
    def __init__(self, conf, exchange, state=None):
        self.conf, self.exchange = conf, exchange
        if conf['dca']['side'] not in {'buy', 'sell'} or number(conf['dca']['size']) <= 0 or number(conf['dca']['freq']) <= 0:
            raise ValueError('DCA needs buy or sell, a positive size and a positive interval in seconds')
        self.state = state or State(initial={'strategy': conf, 'sequence': 0, 'pending': None, 'next_due': 0, 'executions': []})
        if self.state.data['strategy'] != conf:
            raise ValueError('Strategy differs from saved state')

    def tick(self, now=None):
        now = time.time() if now is None else now
        d = self.state.data
        if d['pending'] is None:
            if now < d['next_due']:
                return
            d['pending'] = self.exchange.place(f'dca:{d["sequence"]}', self.conf['main']['market'], self.conf['dca']['side'].upper(), self.conf['dca']['size'], slippage=self.conf['dca']['slippage'])
            self.state.save()
        result = self.exchange.status(d['pending'])
        if result['status'] not in TERMINAL:
            return
        quantity, price, fee = self.exchange.execution(d['pending'])
        d['executions'].append({'size': str(quantity), 'price': str(price), 'fee': str(fee), 'at': now})
        d['pending'] = None
        d['sequence'] += 1
        d['next_due'] = now + float(self.conf['dca']['freq'])
        self.state.save()
        log(f"{self.conf['dca']['side']} executed size {quantity} at {price}; fee {fee}", self.conf['main']['name'])


def main():
    conf = load_config()
    with single_instance():
        exchange = Exchange(conf['exchange'])
        try:
            bot = DCA(conf, exchange)
            while True:
                bot.tick()
                time.sleep(conf['exchange']['poll_seconds'])
        finally:
            exchange.close()


if __name__ == '__main__':
    main()
