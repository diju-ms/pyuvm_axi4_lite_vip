import cocotb
import os
import random
import csv
from pyuvm import *
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

from vip.axi_lite_item import AxiLiteItem
from vip.axi_lite_agent import AxiLiteAgent
from vip.axi_lite_scoreboard import AxiScoreboard


# ===================================================================
# 🎬 Sequence & Env & Test (测试平台专属逻辑)
# ===================================================================
class SanitySeq(uvm_sequence):
    async def body(self):
        reg_map = ConfigDB().get(None, "", "GLOBAL_REG_MAP")
        if reg_map:
            addr_list = list(reg_map.keys())
        else:
            addr_list = [0x0, 0x4, 0x8, 0xC]

        for _ in range(1000):
            is_write = random.choice([True, False])
            if random.random() < 0.2:
                addr = random.randint(0, 15)
                addr = addr & 0xFFFFFFFC
            else:
                addr = random.choice(addr_list)

            data = random.randint(0, 0xFFFFFFFF) if is_write else 0
            item = AxiLiteItem("stress_item", addr, data, is_write)
            await self.start_item(item)
            await self.finish_item(item)


class AxiEnv(uvm_env):
    def build_phase(self):
        super().build_phase()
        self.agent = AxiLiteAgent("agent", self)
        self.scb = AxiScoreboard("scb", self)

    def connect_phase(self):
        super().connect_phase()
        # 把 Agent 里面 Monitor 广播的大喇叭，连到 Scoreboard 的接收管子上
        self.agent.mon.ap.connect(self.scb.fifo.analysis_export)


@test()
class axi_sanity_test(uvm_test):
    def build_phase(self):
        super().build_phase()
        ConfigDB().set(None, "*", "DUT", cocotb.top)

        self.reg_map = {}
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, "reg_map.csv")
            self.logger.info(f"正在尝试加载配置: {csv_path}")
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    addr = int(row["ADDR"].strip(), 16)
                    reset_val = int(row["RESET_VALUE"].strip(), 16)
                    self.reg_map[addr] = reset_val
        except Exception as e:
            self.logger.error(f"读取 CSV 失败: {e}")

        ConfigDB().set(None, "*", "GLOBAL_REG_MAP", self.reg_map)
        self.env = AxiEnv("env", self)

    async def run_phase(self):
        dut = cocotb.top
        cocotb.start_soon(Clock(dut.S_AXI_ACLK, 10, unit="ns").start())
        self.raise_objection()

        dut.S_AXI_ARESETN.value = 0
        await Timer(20, unit="ns")
        dut.S_AXI_ARESETN.value = 1
        await RisingEdge(dut.S_AXI_ACLK)

        self.logger.info("🚀 ========================================")
        self.logger.info("🔥 AXI4-Lite VIP 启动：开始压力测试")
        self.logger.info("🚀 ========================================")

        seq = SanitySeq("seq")
        # 启动 Sequence 时，交给 Agent 内部的 Sequencer 执行
        await seq.start(self.env.agent.seqr)

        await Timer(50, unit="ns")
        self.drop_objection()