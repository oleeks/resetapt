import os
import sys
import configparser


EDITION_SOURCES_FILES = dict(
    default="/etc/apt/sources.list",
    appstore="/etc/apt/sources.list.d/appstore.list",
    printer="/etc/apt/sources.list.d/printer.list",
)

DEFAULT_OPEN_SOURCES = dict(
Community=dict(
    default="deb [by-hash=force] https://community-packages.deepin.com/deepin/ apricot main contrib non-free\n",
    appstore="deb https://community-store-packages.deepin.com/appstore eagle appstore\n",
    printer="deb https://community-packages.deepin.com/printer eagle non-free"
),
Home=dict(
    default="deb [by-hash=force] https://home-packages.chinauos.com/home plum main contrib non-free\n",
    appstore="deb https://home-store-packages.chinauos.com/appstore eagle appstore\n",
    printer="deb https://home-packages.chinauos.com/printer eagle non-free\n"
),
Professional=dict(
    default="deb [by-hash=force] https://home-packages.chinauos.com/desktop-professional plum main contrib non-free\n",
    appstore="deb https://home-store-packages.chinauos.com/appstore eagle appstore\n",
    printer="deb https://home-packages.chinauos.com/printer eagle non-free\n"
),
)


cf = configparser.ConfigParser()


class ResetAptSources:
    source_types = ("default", "appstore", "printer")

    def __init__(self, os_version_path='/etc/os-version'):
        self.os_version_file = os_version_path
        self.default_open_sourc = self.get_default_open_source()
        self.reset = False
    
    @staticmethod
    def get_auth():
        """
        获取系统权限
        """
        euid = os.geteuid()
        if euid != 0:
            args = ['sudo', sys.executable] + sys.argv + [os.environ]
            # replaces the currently-running process with the seixtudo
            os.execlpe('sudo', *args)

    def get_os_edition_name(self):
        """
        获取系统版本信息
        """
        try:
            cf.read(self.os_version_file)
        except FileNotFoundError:
            print('当前系统不是Deepin社区版、UOS个人版或专业版')
        
        return cf.get('Version', 'EditionName')

    def get_default_open_source(self):
        os_edition_name = self.get_os_edition_name()
        print(os_edition_name)
        return DEFAULT_OPEN_SOURCES.get(os_edition_name)

    @staticmethod
    def read_sources(file_path):
        """
        读取当前系统源数据
        """
        content = ""
        try:
            with open(file_path) as src:
                for line in src.readlines():
                    line_strip = line.strip()
                    if line_strip.startswith("#"):
                        continue
                    content += line_strip
        except FileNotFoundError:
            print(file_path, '文件不存在')
            exit()
  
        return content

    @staticmethod
    def get_source_file_path(source_type):
        """
        获取不同类型源文件的路径
        """
        return EDITION_SOURCES_FILES.get(source_type)
    
    def current_comparison_reset(self, source_type):
        """
        源对比并重置
        """
        source_file_path = self.get_source_file_path()
        print("正在当前检查的是 {}, 源文件{}".format(source_type, source_file_path))
        current_sources_content = self.read_sources(source_file_path)
        default_sources_content = self.default_open_sourc[source_type].strip()
        
        if default_sources_content == current_sources_content:
            print("源文件未被修改")
            return None
        
        agree = self.user_agree_to_reset(source_file_path)

        if agree:
            self.save_source_file(source_file_path, default_sources_content)
            self.reset = True
    
    def save_source_file(source_file_path, reset_content):
        with open(source_file_path, 'w') as f:
            f.write(reset_content)

    @staticmethod
    def user_agree_to_reset(source_file_path):
        prompt_msg = "源文件 '" + source_file_path + "' 已被修改，是否重置？(Y/n): "
        r = 'Y'
        while (r != 'y' and r != 'n' and r != ''):
            r = input(prompt_msg).lower()
        return r != 'n'

    def run(self):
        """
        运行
        """
        self.get_auth()

        for source_type in self.source_types:
            self.current_comparison_reset(source_type)

        if self.reset:
            os.system('apt update -y && apt upgrade -y')

if __name__ == "__main__":
    reset = ResetAptSources()
    reset.run()
