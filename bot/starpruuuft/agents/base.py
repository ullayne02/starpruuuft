from sc2.constants import *

from bot.starpruuuft.agent_message import AgentMessage
from .agent import Agent
from .. import utilities


class BaseAgent(Agent):
    def __init__(self, bot):
        super().__init__(bot)

        self.add_message_handler(AgentMessage.BARRACKS_READY, self._handle_upgrade_ready)

        # Indica se o CC deve parar de treinar SCVs para liberar espaço na filas
        self._upgrade_command_center_ready = False

    async def on_step(self, bot, iteration):
        # Caso não exista CC, o agente não faz nada
        cc = utilities.get_command_center(bot)
        if cc is None:
            return

        await self._train_scvs(bot, cc)
        await self._calldown_mule(bot, cc)

    # Atualiza o estado para marcar que o upgrade para orbital já pode ser realizado
    def _handle_upgrade_ready(self, *args):
        self._upgrade_command_center_ready = True

    async def _train_scvs(self, bot, cc):
        # Tenta esvaziar a fila para fazer upgrade
        halt = self._upgrade_command_center_ready and cc.type_id is not UnitTypeId.ORBITALCOMMAND

        # API não retorna corretamente a quantidade de workers, diferença de 2 observada
        train = bot.supply_left > 0 and bot.workers.amount < (23 - 2)

        if halt or not train:
            return

        if cc.noqueue and bot.can_afford(UnitTypeId.SCV):
            await bot.do(cc.train(UnitTypeId.SCV))

    async def _calldown_mule(self, bot, cc):
        # Apenas se já for orbital e tiver energia suficiente
        calldown = cc.type_id is UnitTypeId.ORBITALCOMMAND and cc.energy >= 50

        if not calldown:
            return

        target = bot.state.mineral_field.closest_to(cc).position.to2
        await bot.do(cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target))

