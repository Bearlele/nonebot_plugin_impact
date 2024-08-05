"""matcher的handle模块"""
import asyncio
import random
import time
import math
from random import choice
from typing import Dict, List, Tuple

from httpx import AsyncClient
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, RegexGroup

from .data_sheet import (
    add_new_user,
    check_group_allow,
    get_ejaculation_data,
    get_jj_length,
    get_sorted,
    get_today_ejaculation_data,
    insert_ejaculation,
    is_in_table,
    punish_all_inactive_users,
    set_group_allow,
    set_jj_length,
    update_activity,
    set_jjlock,
    get_jjlock,
    calculate_difference_and_penalty,
)
from .draw_img import draw_bar_chart
from .utils import utils
from datetime import datetime


class Impart:
    penalties_impact: bool = getattr(
        get_driver().config, "isalive", False
    )  # 重置每日活跃度

    @staticmethod
    def penalties_and_resets() -> None:
        """重置每日活跃度"""
        if Impart.penalties_impact:
            punish_all_inactive_users()

    @staticmethod
    async def pk(matcher: Matcher, event: GroupMessageEvent) -> None:
        """pk的响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()
        at = await utils.get_at(event)  # 获取at的id, 类型为str
        # rule规定了必须有at, 所以不用判断at是否为寄
        if is_in_table(userid=int(uid)) and is_in_table(int(at)):  # 如果两个都在userdata里面
            if at == uid:  # 如果at的id和uid相同, 则返回
                await matcher.finish("你不能pk自己喵", at_sender=True)

            allow: bool = await utils.pkcd_check(uid)  # CD是否允许pk
            if not allow:  # 如果不允许pk, 则返回
                await matcher.finish(
                    f"你已经pk不动了喵, 请等待{round(utils.pk_cd_time-(time.time() - utils.pk_cd_data[uid]),3)}秒后再pk喵",
                    at_sender=True,
                )

            jjlock_info = get_jjlock(at)
            if jjlock_info[0]:
                await matcher.finish(
                    f"对方的{choice(utils.jj_variable)}被锁上了，无法发起攻击喵",
                    at_sender=True,
                )
            
            # ============= 战斗 ==============
            utils.pk_cd_data.update({uid: time.time()})  # 更新CD时间
            values = [get_jj_length(int(uid)), get_jj_length(int(at))]
            values.sort()
            # 确保 min_value 和 max_value 是正数并且在合理范围内
            min_value = max(1, abs(int(values[0])))  # 确保不小于 1
            max_value = min(100, abs(int(values[1] * 10)))  # 确保不超过 100

            # 确保 min_value 小于或等于 max_value
            if min_value > max_value:
                min_value, max_value = max_value, min_value

            # 如果 min_value 和 max_value 仍然无效，设置默认值
            if min_value == 0 or max_value == 0 or min_value > max_value:
                min_value, max_value = 1, 100

            # 确保 divisor 不为 0
            divisor = random.randint(min_value, max_value)
            while divisor == 0:
                divisor = random.randint(min_value, max_value)

            P = 1 / (1 + math.exp(-(get_jj_length(int(uid)) - get_jj_length(int(at))) / divisor))
            random_num = round(random.random())

            # ============= 随机事件 ==============
            # 将最小值映射到0到1的范围内
            min_range = -50
            max_range = 0
            trigger_probability = max(0, min(1, (max_range - values[0]) / (max_range - min_range)))
            if (get_jj_length(int(uid)) <= 0 or get_jj_length(int(at)) <= 0):
                if (random.random() < trigger_probability):
                    print("[淫趴] 触发随机事件——— 雌堕")
                    P = P * random.randint(7, 20)
                    if uid <= at:
                        set_jj_length(int(at), -P)
                        await matcher.finish(
                            f"你触发了‘雌堕’效果，对方{choice(utils.jj_variable)}在你的攻击下无法逃脱，受到高额伤害，减小了{round(P,3)}cm喵",
                            at_sender=True,
                        )
                    else:
                        set_jj_length(int(uid), -P)
                        await matcher.finish(
                            f"你尝试攻击对方的{choice(utils.jj_variable)}，很不幸对方触发了‘雌堕’效果，你的{choice(utils.jj_variable)}受到高额伤害，减小了{round(P,3)}cm喵",
                            at_sender=True,
                        )
            
            # ============= 正常战斗 ==============
            if random_num <= P:
                # random_num: float = utils.get_random_num()  # 重新生成一个随机数
                set_jj_length(int(uid), P / 2)
                set_jj_length(int(at), -P)
                await matcher.finish(
                    f"对决胜利喵, 你的{choice(utils.jj_variable)}增加了{round(P/2,3)}cm喵, 对面则在你的阴影笼罩下减小了{round(P,3)}cm喵",
                    at_sender=True,
                )
            else:
                # random_num: float = utils.get_random_num()  # 重新生成一个随机数
                set_jj_length(int(uid), -P)
                set_jj_length(int(at), P / 2)
                await matcher.finish(
                    f"对决失败喵, 在对面牛子的阴影笼罩下你的{choice(utils.jj_variable)}减小了{round(P,3)}cm喵, 对面增加了{round(P/2,3)}cm喵",
                    at_sender=True,
                )
        else:
            # 谁不在userdata里面, 就创建谁
            if is_in_table(userid=int(uid)):
                add_new_user(int(at))
            if is_in_table(userid=int(at)):
                add_new_user(int(uid))
            del utils.pk_cd_data[uid]  # 删除CD时间
            await matcher.finish(
                f"你或对面还没有创建{choice(utils.jj_variable)}喵, 咱全帮你创建了喵, 你们的{choice(utils.jj_variable)}长度都是10cm喵",
                at_sender=True,
            )

    @staticmethod
    async def dajiao(matcher: Matcher, event: GroupMessageEvent) -> None:
        """打胶的响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()
        allow = await utils.cd_check(uid)  # CD是否允许打胶
        if not allow:  # 如果不允许打胶, 则返回
            await matcher.finish(
                f"你已经打不动了喵, 请等待{round(utils.dj_cd_time-(time.time() - utils.cd_data[uid]),3)}秒后再打喵",
                at_sender=True,
            )
        utils.cd_data.update({uid: time.time()})  # 更新CD时间
        if is_in_table(userid=int(uid)):  # 如果在userdata里面
            random_num = utils.get_random_num()  # 生成一个随机数
            set_jj_length(int(uid), random_num)  # 更新userdata
            await matcher.finish(
                f"打胶结束喵, 你的{choice(utils.jj_variable)}很满意喵, 长了{random_num}cm喵, 目前长度为{get_jj_length(int(uid))}cm喵",
                at_sender=True,
            )
        else:
            add_new_user(int(uid))  # 创建用户
            await matcher.finish(
                f"你还没有创建{choice(utils.jj_variable)}, 咱帮你创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )

    @staticmethod
    async def suo(matcher: Matcher, event: GroupMessageEvent) -> None:
        """嗦牛子的响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()
        allow = await utils.suo_cd_check(uid)  # CD是否允许嗦
        if not allow:  # 如果不允许嗦, 则返回
            await matcher.finish(
                f"你已经嗦不动了喵, 请等待{round(utils.suo_cd_time-(time.time() - utils.suo_cd_data[uid]),3)}秒后再嗦喵",
                at_sender=True,
            )
        utils.suo_cd_data.update({uid: time.time()})  # 更新CD时间
        at: str = await utils.get_at(event)  # 获取at的用户id, 类型为str
        if at == "寄":  # 如果没有at
            if is_in_table(userid=int(uid)):  # 如果在userdata里面
                random_num = utils.get_random_num()  # 生成一个随机数
                set_jj_length(int(uid), random_num)
                await matcher.finish(
                    f"你的{choice(utils.jj_variable)}很满意喵, 嗦长了{random_num}cm喵, 目前长度为{get_jj_length(int(uid))}cm喵",
                    at_sender=True,
                )
            else:  # 如果不在userdata里面
                add_new_user(int(uid))  # 创建用户
                del utils.suo_cd_data[uid]  # 删除CD时间
                await matcher.finish(
                    f"你还没有创建{choice(utils.jj_variable)}喵, 咱帮你创建了喵, 目前长度是10cm喵",
                    at_sender=True,
                )
        elif is_in_table(userid=int(at)):  # 如果在userdata里面
            random_num = utils.get_random_num()  # 生成一个随机数
            # 更新userdata
            set_jj_length(int(at), random_num)
            await matcher.finish(
                f"对方的{choice(utils.jj_variable)}很满意喵, 嗦长了{random_num}cm喵, 目前长度为{get_jj_length(int(at))}cm喵",
                at_sender=True,
            )
        else:
            add_new_user(int(at))  # 创建用户
            del utils.suo_cd_data[uid]  # 删除CD时间
            await matcher.finish(
                f"TA还没有创建{choice(utils.jj_variable)}喵, 咱帮TA创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )

    @staticmethod
    async def queryjj(matcher: Matcher, event: GroupMessageEvent) -> None:
        """查询某人jj的响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()  # 获取用户id, 类型为str
        at: str = await utils.get_at(event)  # 获取at的用户id, 类型为str
        if at == "寄":  # 如果没有at
            if is_in_table(userid=int(uid)):  # 如果在userdata里面
                await matcher.finish(
                    f"你的{choice(utils.jj_variable)}目前长度为{get_jj_length(int(uid))}cm喵",
                    at_sender=True,
                )
            else:
                add_new_user(int(uid))  # 创建用户
                await matcher.finish(
                    f"你还没有创建{choice(utils.jj_variable)}喵, 咱帮你创建了喵, 目前长度是10cm喵",
                    at_sender=True,
                )
        elif is_in_table(userid=int(at)):  # 如果在userdata里面
            await matcher.finish(
                f"TA的{choice(utils.jj_variable)}目前长度为{get_jj_length(int(at))}cm喵",
                at_sender=True,
            )
        else:
            add_new_user(int(at))  # 创建用户
            await matcher.finish(
                f"TA还没有创建{choice(utils.jj_variable)}喵, 咱帮他创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )

    @staticmethod
    async def jjrank(bot: Bot, matcher: Matcher, event: GroupMessageEvent) -> None:
        """输出前五后五和自己的排名"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: int = event.user_id
        rankdata: List[Dict] = get_sorted()
        if len(rankdata) < 5:
            await matcher.finish("目前记录的数据量小于5, 无法显示rank喵")
        top5: List = rankdata[:5]  # 取前5
        last5: List = rankdata[-5:]  # 取后5
        # 获取自己的排名
        index: List = [i for i in range(len(rankdata)) if rankdata[i]["userid"] == uid]
        if not index:  # 如果用户没有创建JJ
            add_new_user(uid)
            await matcher.finish(
                f"你还没有创建{choice(utils.jj_variable)}看不到rank喵, 咱帮你创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )
        # top5和end5的信息，然后获取其网名
        async with AsyncClient() as client:
            top5names = await asyncio.gather(
                *[utils.get_stranger_info(client, name["userid"]) for name in top5]
            )
            last5names = await asyncio.gather(
                *[utils.get_stranger_info(client, name["userid"]) for name in last5]
            )

        data = {top5names[i]: top5[i]["jj_length"] for i in range(len(top5))}
        for i in range(len(last5)):
            data[last5names[i]] = last5[i]["jj_length"]
        img_bytes = await draw_bar_chart.draw_bar_chart(data)
        reply2 = f"你的排名为{index[0]+1}喵"
        await matcher.finish(MessageSegment.image(img_bytes) + reply2, at_sender=True)

    @staticmethod
    async def yinpa_prehandle(
        bot: Bot,
        args: Tuple,
        matcher: Matcher,
        event: GroupMessageEvent,
    ) -> Tuple[int, str, str, list]:
        """透群员的预处理环节"""
        gid, uid = event.group_id, event.user_id
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        allow = await utils.fuck_cd_check(event)  # CD检查是否允许
        if not allow:
            await matcher.finish(
                f"你已经榨不出来任何东西了, 请先休息{round(utils.fuck_cd_time-(time.time() - utils.ejaculation_cd[str(uid)]),3)}秒",
                at_sender=True,
            )
        utils.ejaculation_cd.update({str(uid): time.time()})  # 记录时间
        req_user_card: str = str(event.sender.card or event.sender.nickname)
        prep_list = await bot.get_group_member_list(group_id=gid)
        return uid, req_user_card, args[0], prep_list

    @staticmethod
    async def yinpa_member_handle(
        prep_list: list,
        req_user_card: str,
        matcher: Matcher,
        event: GroupMessageEvent,
    ) -> str:
        prep_list = [prep.get("user_id", 114514) for prep in prep_list]  # 群友列表
        target = await utils.get_at(event)  # 获取消息有没有at
        if target == "寄":  # 没有的话
            # 随机抽取幸运成员
            prep_list.remove(event.user_id)
            lucky_user = choice(prep_list)
            await matcher.send(
                f"现在咱将随机抽取一位幸运群友\n送给{req_user_card}色色！"
            )
        else:  # 有的话lucky user就是at的人
            lucky_user = target
        return lucky_user

    @staticmethod
    async def yinpa_owner_handle(
        uid: int,
        prep_list: list,
        req_user_card: str,
        matcher: Matcher,
    ) -> str:
        lucky_user: str = next(
            ((prep["user_id"]) for prep in prep_list if prep["role"] == "owner"),
            str(uid),
        )
        if int(lucky_user) == uid:  # 如果群主是自己
            del utils.ejaculation_cd[str(uid)]
            await matcher.finish("你透你自己?")
        await matcher.send(f"现在咱将把群主\n送给{req_user_card}色色！")
        return lucky_user

    @staticmethod
    async def yinpa_admin_handle(
        uid: int,
        prep_list: list,
        req_user_card: str,
        matcher: Matcher,
    ) -> str:
        admin_id: list = [
            prep["user_id"] for prep in prep_list if prep["role"] == "admin"
        ]
        if uid in admin_id:  # 如果自己是管理的话， 移除自己
            admin_id.remove(uid)
        if not admin_id:  # 如果没有管理的话, del cd信息， 然后finish
            del utils.ejaculation_cd[str(uid)]
            await matcher.finish("喵喵喵? 找不到群管理!")
        lucky_user: str = choice(admin_id)  # random抽取一个管理
        await matcher.send(f"现在咱将随机抽取一位幸运管理\n送给{req_user_card}色色！")
        return lucky_user

    async def yinpa_identity_handle(
        self,
        command: str,
        prep_list: list,
        req_user_card: str,
        matcher: Matcher,
        event: GroupMessageEvent,
    ) -> str:
        uid: int = event.user_id
        if "群主" in command:  # 如果发送的命令里面含有群主， 说明在透群主
            return await self.yinpa_owner_handle(uid, prep_list, req_user_card, matcher)
        elif "管理" in command:  # 如果发送的命令里面含有管理， 说明在透管理
            return await self.yinpa_admin_handle(uid, prep_list, req_user_card, matcher)
        else:  # 最后是群员
            return await self.yinpa_member_handle(
                prep_list, req_user_card, matcher, event
            )

    async def yinpa(
        self,
        bot: Bot,
        matcher: Matcher,
        event: GroupMessageEvent,
        args: Tuple = RegexGroup(),
    ) -> None:
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid, req_user_card, command, prep_list = await self.yinpa_prehandle(
            matcher=matcher, bot=bot, args=args, event=event
        )
        lucky_user: str = await self.yinpa_identity_handle(
            command=command,
            prep_list=prep_list,
            req_user_card=req_user_card,
            matcher=matcher,
            event=event,
        )
        lucky_user_card = next(
            (
                prep["card"] or prep["nickname"]
                for prep in prep_list
                if prep["user_id"] == int(lucky_user)
            ),
            "群友",
        )
        # 1--100的随机数， 保留三位
        ejaculation = round(random.uniform(1, 100), 3)
        insert_ejaculation(int(lucky_user), ejaculation)
        await asyncio.sleep(2)  # 休眠2秒, 更有效果
        update_activity(int(lucky_user))  # 更新活跃度
        update_activity(uid)  # 更新活跃度
        # 准备调用api, 用来获取头像
        repo_1 = f"好欸！{req_user_card}({uid})用时{random.randint(1, 20)}秒 \n给 {lucky_user_card}({lucky_user}) 注入了{ejaculation}毫升的脱氧核糖核酸, 当日总注入量为：{get_today_ejaculation_data(int(lucky_user))}毫升\n"
        await matcher.send(
            repo_1
            # + MessageSegment.image(f"https://q1.qlogo.cn/g?b=qq&nk={lucky_user}&s=640")
        )  # 结束

    @staticmethod
    async def open_module(
        matcher: Matcher, event: GroupMessageEvent, args: Tuple = RegexGroup()
    ) -> None:
        """开关"""
        gid: int = event.group_id
        command: str = args[0]
        if "开启" in command or "开始" in command:
            set_group_allow(gid, True)
            await matcher.finish("功能已开启喵")
        elif "禁止" in command or "关闭" in command:
            set_group_allow(gid, False)
            await matcher.finish("功能已禁用喵")

    @staticmethod
    async def query_injection(
        matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()
    ) -> None:
        """查询某人的注入量"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        target = args.extract_plain_text()  # 获取命令参数
        user_id: str = event.get_user_id()
        # 判断带不带at
        [object_id, replay1] = (
            [await utils.get_at(event), "该用户"]
            if await utils.get_at(event) != "寄"
            else [user_id, "您"]
        )
        #  获取用户的所有注入数据
        data: List[Dict] = get_ejaculation_data(int(object_id))
        ejaculation = 0  # 先初始化0
        if "历史" in target or "全部" in target:
            if not data:
                await matcher.finish(f"{replay1}历史总被注射量为0ml")
            inject_data = {}
            for item in data:  # 遍历所有的日期
                temp: float = item["volume"]  # 获取注入量
                ejaculation += temp  # 注入量求和
                date: str = item["date"]  # 获取日期
                inject_data[date] = temp
            if len(inject_data) < 2:
                await matcher.finish(f"{replay1}历史总被注射量为{ejaculation}ml")

            await matcher.finish(
                MessageSegment.text(f"{replay1}历史总被注射量为{ejaculation}ml")
                + MessageSegment.image(
                    await draw_bar_chart.draw_line_chart(inject_data)
                )
            )
        else:
            ejaculation: float = get_today_ejaculation_data(int(object_id))
            await matcher.finish(f"{replay1}当日总被注射量为{ejaculation}ml")

    @staticmethod
    async def yinpa_introduce(matcher: Matcher) -> None:
        """输出用法"""
        await matcher.send(MessageSegment.image(await utils.plugin_usage()))

    @staticmethod
    async def jjlock(matcher: Matcher, event: GroupMessageEvent) -> None:
        """贞操锁上锁响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()
        if is_in_table(userid=int(uid)):  # 如果在userdata里面
            jj_length = get_jj_length(int(uid))
            print (f"[银趴DEBUG] {jj_length}")
            if jj_length > 2:
                jjlock_info = get_jjlock(uid)
                if jjlock_info[0]:
                    readable_diff, hours_diff = calculate_difference_and_penalty(datetime.strptime(jjlock_info[1], '%Y-%m-%d %H:%M:%S'))
                    await matcher.finish(
                        f"你的{choice(utils.jj_variable)}已经是锁定状态了喵，锁定时长{readable_diff}，想要解锁可以发送‘jj解锁’喵",
                        at_sender=True,
                    )
                else: 
                    set_jjlock(uid, True)
                    await matcher.finish(
                            f"你的{choice(utils.jj_variable)}已经成功锁上了喵，锁太久会对{choice(utils.jj_variable)}造成不可逆的损伤，想要解锁可以发送‘jj解锁’喵",
                            at_sender=True,
                        )
            else:
                await matcher.finish(
                    f"你的{choice(utils.jj_variable)}只剩{round(jj_length, 3)}cm，锁不上喵",
                    at_sender=True,
                )
        else:
            add_new_user(int(uid))  # 创建用户
            await matcher.finish(
                f"你还没有创建{choice(utils.jj_variable)}, 咱帮你创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )

    @staticmethod
    async def jjunlock(matcher: Matcher, event: GroupMessageEvent) -> None:
        """贞操锁解锁响应器"""
        if not check_group_allow(event.group_id):
            await matcher.finish(utils.not_allow, at_sender=True)
        uid: str = event.get_user_id()
        if is_in_table(userid=int(uid)):  # 如果在userdata里面
            jjlock_info = get_jjlock(uid)
            if jjlock_info[0]:
                """计算从锁定时间到现在的惩罚值"""
                readable_diff, hours_diff = calculate_difference_and_penalty(datetime.strptime(jjlock_info[1], '%Y-%m-%d %H:%M:%S'))
                print (f"[银趴] {readable_diff} {hours_diff}")
                if hours_diff > 1:
                    minutes_over = (hours_diff - 1) * 60
                    penalty = min(minutes_over * random.uniform(0.005, 0.008), get_jj_length(uid) - 2) # 惩罚后最短不小于2cm
                    set_jj_length(int(uid), -penalty)
                    set_jjlock(uid, False)
                    await matcher.finish(
                        f"你的{choice(utils.jj_variable)}已经成功解锁了喵，锁定时长{readable_diff}已对{choice(utils.jj_variable)}造成了不可逆的伤害，减小了{round(penalty,3)}cm喵",
                        at_sender=True,
                    ) 

                set_jjlock(uid, False)
                await matcher.finish(
                        f"你的{choice(utils.jj_variable)}已经成功解锁了喵，锁定时长{readable_diff}",
                        at_sender=True,
                    )
            else:
                await matcher.finish(
                        f"你的{choice(utils.jj_variable)}没有被锁上不需要解锁喵",
                        at_sender=True,
                    )
        else:
            add_new_user(int(uid))  # 创建用户
            await matcher.finish(
                f"你还没有创建{choice(utils.jj_variable)}, 咱帮你创建了喵, 目前长度是10cm喵",
                at_sender=True,
            )

    


impart = Impart()
