params:args||{};EventsGame.play(action);handlers[action]||function(args){return flow._act(action,args)};
flow.setActionHandler("spin",function(args){args=args||{};args.bet_per_line="bet_per_line"in args?args.bet_per_line:_this3.app.model.betPerLine();args.lines="lines"in args?args.lines:_this3.app.model.gameLines();_this3.app.model.setBetPerLine(args.bet_per_line);_this3.app.model.setLines(args.lines);return _this3._act("spin",args,_this3.app.model.getRoundBet(args.bet_per_line,args.lines))});
flow.setActionHandler("respin",function(args){if(!_app.default.model.canAction("respin")){return Promise.reject(new Error("action not allowed"))}_app.default.emit(_Enums.GameEvent.BonusRoundStart);return _app.default.flow._act("respin",args)});
app.flow.act("bonus_init");
app.flow.act("respin");
app.flow.act("freespin");
app.flow.act("bonus_".concat(app.model.bonusOriginState(),"_stop"));
this._get("game.bonus.back_to","spins");