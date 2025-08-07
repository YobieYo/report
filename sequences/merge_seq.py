from data_loaders.abstract_loader import AbstractLoader
from report_builders.abstract_drawer import AbstractDrawer
from db.repositories import program_repository, tractor_repository
import time

class MergeSequence:
    def __init__(self, loader : AbstractLoader, report_builder : AbstractDrawer):
        self.loader = loader
        self.report_builder = report_builder


    def run(self):
        if self.loader:
            start_load_prog = time.time()
            self.loader.load_programs()
            stop_load_prog = time.time()

            start_load_trac = time.time()
            self.loader.load_tractors()
            stop_load_trac = time.time()

            start_load_dep = time.time()
            self.loader.load_departments()
            stop_load_dep = time.time()

            start_load_rep = time.time()
            self.loader.create_reports()
            stop_load_rep = time.time()

            start_draw = time.time()
            self.report_builder.draw()
            stop_draw = time.time()

            print(f"Программы загрузили за {(stop_load_prog - start_load_prog):.4f} секунд")
            print(f"Тракторы загрузили за {(stop_load_trac - start_load_trac):.4f} секунд")
            print(f"Отделы загрузили за {(stop_load_dep - start_load_dep):.4f} секунд")
            print(f"Отчеты создали за {(stop_load_rep - start_load_rep):.4f} секунд")
            print(f"Графики построили за {(stop_draw - start_draw):.4f} секунд")
            print("="*50)
            print(f"Общее время выполнения: {((stop_draw - start_load_prog)):.4f} секунд")

            print('всего программ',len(program_repository.get_all()))
            print('всего тракторов', len(tractor_repository.get_all()))
            k = 0
            for tractor in tractor_repository.get_all():
                if tractor.programs:
                    k += 1
            print('всего тракторов с программами', k)
            programs = program_repository.get_all()
            print('активных программ', len(program_repository.get_active_programs()))



            
