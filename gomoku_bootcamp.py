import copy
import re
from internbootcamp.base import BaseBootcamp

class GomokuBootcamp(BaseBootcamp):
    """
    五子棋 InternBootCamp 环境类。
    实现了五子棋的游戏逻辑，包括棋盘初始化、落子、胜负判断和提示生成。
    """
    def __init__(self, board_size=15):
        """
        初始化五子棋游戏环境。

        Args:
            board_size (int): 棋盘的尺寸，默认为15x15。
        """
        super().__init__()
        self.board_size = board_size
        # 棋盘状态，0代表空位，1代表玩家1（黑棋），2代表玩家2（白棋）
        self.board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self.current_player = 1  # 1代表玩家1先手

    def case_generator(self):
        """
        生成一个新的五子棋游戏案例。
        重置棋盘和当前玩家。

        Returns:
            dict: 包含初始棋盘状态和当前玩家的字典。
        """
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = 1
        return {
            'board': copy.deepcopy(self.board),
            'current_player': self.current_player
        }

    def prompt_func(self, identity):
        """
        根据当前棋局状态生成给大语言模型的提示。

        Args:
            identity (dict): 包含当前棋盘 ('board') 和当前玩家 ('current_player') 的字典。

        Returns:
            str: 格式化后的提示字符串。
        """
        board = identity['board']
        current_player = identity['current_player']

        # 将二维列表棋盘转换为字符串表示
        board_str = "\n".join([" ".join(map(str, row)) for row in board])

        player_color = "黑棋" if current_player == 1 else "白棋"

        prompt = (
            f"这是一个{self.board_size}x{self.board_size}的五子棋棋盘。0代表空位，1代表玩家1（黑棋）的棋子，2代表玩家2（白棋）的棋子。\n"
            f"当前棋盘状态如下：\n{board_str}\n"
            f"现在轮到玩家{current_player} (执{player_color}) 下子。\n"
            f"请给出你的落子坐标，格式为 (行,列)，其中行和列的索引都从0开始。例如：(7,7)。"
        )
        return prompt

    @classmethod
    def _check_win(cls, board, player, r, c, board_size):
        """
        辅助方法：检查给定玩家在 (r, c) 落子后是否形成五子连珠。

        Args:
            board (list[list[int]]): 当前棋盘状态。
            player (int): 要检查的玩家 (1或2)。
            r (int): 最近落子的行坐标。
            c (int): 最近落子的列坐标。
            board_size (int): 棋盘尺寸。

        Returns:
            bool: 如果形成五子连珠则返回 True，否则返回 False。
        """
        directions = [
            (0, 1),   # 水平
            (1, 0),   # 垂直
            (1, 1),   # 主对角线 (左上到右下)
            (1, -1)   # 副对角线 (右上到左下)
        ]

        for dr, dc in directions:
            count = 1
            # 向一个方向检查
            for i in range(1, 5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < board_size and 0 <= nc < board_size and board[nr][nc] == player:
                    count += 1
                else:
                    break
            # 向相反方向检查
            for i in range(1, 5):
                nr, nc = r - dr * i, c - dc * i
                if 0 <= nr < board_size and 0 <= nc < board_size and board[nr][nc] == player:
                    count += 1
                else:
                    break
            if count >= 5:
                return True
        return False

    @classmethod
    def verify_score(cls, response, identity, format_score=0):
        """
        验证大语言模型的响应，计算得分并更新棋局状态。

        Args:
            response (str): 大语言模型给出的响应字符串。
            identity (dict): 包含当前棋盘 ('board') 和当前玩家 ('current_player') 的字典。
            format_score (int): 格式化得分，此处未使用。

        Returns:
            tuple: (得分, 更新后的 identity 字典)。
                   得分：
                   -1.0: 响应格式不正确或无法解析。
                   -10.0: 落子不合法（越界或位置已被占据）。
                   +100.0: 当前玩家获胜。
                   0.0: 平局。
                   +1.0: 落子合法，游戏继续。
        """
        # 尝试从response中解析出 (行,列) 格式的坐标
        match = re.search(r'\((\d+),\s*(\d+)\)', response)
        if not match:
            # 无法解析出坐标，返回负分，状态不变
            return -1.0, identity 

        try:
            row = int(match.group(1))
            col = int(match.group(2))
        except ValueError:
            # 解析出的不是有效数字，返回负分
            return -1.0, identity 

        board = identity['board']
        current_player = identity['current_player']
        board_size = len(board) # 假设棋盘是正方形

        # 检查落子是否合法
        if not (0 <= row < board_size and 0 <= col < board_size):
            return -10.0, identity # 越界
        if board[row][col] != 0:
            return -10.0, identity # 位置已被占据

        # 执行落子并创建新棋局状态
        new_board = copy.deepcopy(board)
        new_board[row][col] = current_player

        # 判断是否获胜
        if cls._check_win(new_board, current_player, row, col, board_size):
            return 100.0, {
                'board': new_board,
                'current_player': current_player,
                'game_over': True,
                'winner': current_player
            }

        # 判断是否平局 (棋盘已满)
        is_draw = all(cell != 0 for row in new_board for cell in row)
        if is_draw:
            return 0.0, {
                'board': new_board,
                'current_player': current_player,
                'game_over': True,
                'winner': None # None表示平局
            }

        # 游戏继续
        next_player = 3 - current_player # 1 -> 2, 2 -> 1 切换玩家
        return 1.0, {
            'board': new_board,
            'current_player': next_player,
            'game_over': False
        }

