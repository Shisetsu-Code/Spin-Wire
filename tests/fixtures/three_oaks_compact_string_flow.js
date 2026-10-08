getActionHandler(e){return this.handlers[e]||(t=>this._act(e,t))};
initDefaultMiddleware(){this.setActionHandler(bn.SPIN,e=>((e=e||{}).bet_per_line="bet_per_line"in e?e.bet_per_line:this.app.model.betPerLine(),e.lines="lines"in e?e.lines:this.app.model.gameLines(),e.bet_factor="bet_factor"in e?e.bet_factor:this.app.model.betFactor()[0],this.app.model.setBetPerLine(e.bet_per_line),this.app.model.setLines(e.lines),this.app.model.setBetFactor(e.bet_factor),this._act(bn.SPIN,e,this.app.model.getRoundBet(e.bet_per_line,e.bet_factor)))),this.setActionHandler(bn.BUY_SPIN,e=>((e=e||{}).bet_per_line="bet_per_line"in e?e.bet_per_line:this.app.model.betPerLine(),e.lines="lines"in e?e.lines:this.app.model.gameLines(),e.bet_factor="bet_factor"in e?e.bet_factor:this.app.model.betFactor()[0],this.app.model.setBetPerLine(e.bet_per_line),this.app.model.setLines(e.lines),this.app.model.setBetFactor(e.bet_factor),this._act(bn.BUY_SPIN,e,this.app.model.freespinsBuyingPrice()*this.app.model.getRoundBet(e.bet_per_line,e.bet_factor)))),this.app.config.get(G.BONUS_GAME.available)&&(this.setActionHandler(bn.RESPIN,e=>this.app.model.canAction(bn.RESPIN)?(this.app.emit(he.BonusRoundStart),this._act(bn.RESPIN,e)):Promise.reject(new Error("action not allowed"))),X.UiEvents.autogame.on(e=>{e.data&&e.data.active&&this.app.model.canAction(bn.RESPIN)&&this.app.emit(he.BonusRoundStart)}))};
_act(e,t,i=null){let s={action:{name:e,params:t||{}},bet:i};return X.EventsGame.play(s),this.deferred.promise};
actBuyFeature(e){let t={};t.bet_per_line=GR.UI.model.get("bet_per_line"),t.lines=Fa.model.gameLines(),t.selected_mode=e.toString(),Fa.model.setBuyingPrice(e),Fa.controllers.flow.act(bn.BUY_SPIN,t)};
get BONUS_STOP(){return`bonus_${Fa.model.bonusOriginState()}_stop`};
.actIfPossible(bn.FREESPIN_INIT);
.act(bn.FREESPIN);
.actIfPossible(bn.FREESPIN_STOP);
.act(bn.BONUS_INIT);
.act(bn.RESPIN);
.act(bn.BONUS_STOP);
bonusOriginState(){return this._get("game.bonus.back_to","spins")}