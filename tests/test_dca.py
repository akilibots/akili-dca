from app import DCA
from runtime import State, number


def test_schedule_persists_and_does_not_catch_up(conf, fake, state_dir):
    conf['dca']['freq'] = 30
    bot = DCA(conf, fake)
    bot.tick(100)
    assert len(fake.calls) == 1
    fake.fill('dca:0')
    bot.tick(100)
    assert bot.state.data['next_due'] == 130
    bot = DCA(conf, fake, State())
    bot.tick(120)
    assert len(fake.calls) == 1
    bot.tick(1000)
    assert len(fake.calls) == 2
    assert fake.calls[-1][0] == 'dca:1'


def test_sell_and_partial_ioc_are_recorded(conf, fake, state_dir):
    conf['dca']['side'] = 'sell'
    bot = DCA(conf, fake)
    bot.tick(100)
    assert fake.calls[0][1][1] == 'SELL'
    fake.fill('dca:0', size='0.0005', status='CANCELED', fee='0.01')
    bot.tick(101)
    assert number(bot.state.data['executions'][0]['size']) == number('0.0005')
    assert len(fake.calls) == 1


def test_crash_after_submission_reuses_order_key(conf, fake, state_dir):
    bot = DCA(conf, fake)
    original = bot.state.save
    def failed_save():
        raise OSError('disk interrupted')
    bot.state.save = failed_save
    try:
        bot.tick(100)
    except OSError:
        pass
    bot = DCA(conf, fake)
    bot.tick(100)
    assert len(fake.calls) == 1
