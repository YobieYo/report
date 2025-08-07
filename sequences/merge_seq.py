from data_loaders.abstract_loader import AbstractLoader
from report_builders.abstract_drawer import AbstractDrawer
from db.repositories import program_repository, tractor_repository

class MergeSequence:
    def __init__(self, loader : AbstractLoader, report_builder : AbstractDrawer):
        self.loader = loader
        self.report_builder = report_builder


    def run(self):
        if self.loader:
            self.loader.load_programs()
            self.loader.load_tractors()
            self.loader.load_departments()
            self.loader.create_reports()
            self.report_builder.draw()

            print('всего программ',len(program_repository.get_all()))
            print('всего тракторов', len(tractor_repository.get_all()))
            k = 0
            for tractor in tractor_repository.get_all():
                if tractor.programs:
                    k += 1
            print('всего тракторов с программами', k)



            
