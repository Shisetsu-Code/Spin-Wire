this.setActionHandler(_constants.FLOW_ACTIONS.SPIN, args => {
      args = args || {};
      args.bet_per_line = 'bet_per_line' in args ? args.bet_per_line : this.app.model.betPerLine();
      args.lines = 'lines' in args ? args.lines : this.app.model.gameLines();
      args.bet_factor = 'bet_factor' in args ? args.bet_factor : this.app.model.betFactor()[0];
      this.app.model.setBetPerLine(args.bet_per_line);
      this.app.model.setLines(args.lines);
      this.app.model.setBetFactor(args.bet_factor);
      return this._act(_constants.FLOW_ACTIONS.SPIN, args, this.app.model.getRoundBet(args.bet_per_line, args.bet_factor));
    });
this.setActionHandler(_constants.FLOW_ACTIONS.BUY_SPIN, args => {
      args = args || {};
      args.bet_per_line = 'bet_per_line' in args ? args.bet_per_line : this.app.model.betPerLine();
      args.lines = 'lines' in args ? args.lines : this.app.model.gameLines();
      args.bet_factor = 'bet_factor' in args ? args.bet_factor : this.app.model.betFactor()[0];
      this.app.model.setBetPerLine(args.bet_per_line);
      this.app.model.setLines(args.lines);
      this.app.model.setBetFactor(args.bet_factor);
      return this._act(_constants.FLOW_ACTIONS.BUY_SPIN, args, this.app.model.freespinsBuyingPrice() * this.app.model.getRoundBet(args.bet_per_line, args.bet_factor));
    });
this.setActionHandler(_constants.FLOW_ACTIONS.RESPIN, args => {
        if (!this.app.model.canAction(_constants.FLOW_ACTIONS.RESPIN)) {
          return Promise.reject(new Error('action not allowed'));
        }
        this.app.emit(_app.GameEvent.BonusRoundStart);
        return this._act(_constants.FLOW_ACTIONS.RESPIN, args);
      });
_act(name, args, bet = null) {
    let action = {
      action: {
        name: name,
        params: args || {}
      },
      bet: bet
    };
    _GameRunnerController.GR.EventsGame.play(action);
    return this.deferred.promise;
  };
getActionHandler(action) {
    return this.handlers[action] || (args => this._act(action, args));
  };
actBuyFeature(buySpineType) {
    _app.default.model.setFreespinsBuyingPrice(_app.default.model.getBuyFeatureCostByType(buySpineType));
    let params = {};
    params.bet_per_line = GR.UI.model.get('bet_per_line');
    params.lines = _app.default.model.betFactor()[0];
    params.selected_mode = buySpineType;
    _app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN, params);
  };
_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.SPIN);