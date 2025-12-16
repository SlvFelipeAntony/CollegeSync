import re

class ValidaDados:

    @staticmethod
    def eh_telefone(str_numero):
        flag = False
        try:
            pattern = r"\(\d{2}\)\d{4,5}-\d{4}"
            flag = bool(re.fullmatch(pattern, str_numero))
        except Exception as e:
            print(e)
        return flag

    @staticmethod
    def get_duration_formatted(self):
        """
        Converte o timedelta do banco para string HH:MM
        Ex: timedelta(seconds=1200) -> '00:20'
        """
        if not self.duration:
            return "00:00:00"

        # Se por acaso já vier como string (ex: erro de tipagem), retorna ela mesma
        if isinstance(self.duration, str):
            return self.duration

        # Pega o total de segundos
        total_seconds = int(self.duration.total_seconds())

        # Calcula horas e minutos
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        # Retorna formatado com dois dígitos (02d)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
