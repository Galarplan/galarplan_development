from odoo import models, api
import logging
import time

_logger = logging.getLogger(__name__)

# Guardar el método create original
_original_create = models.BaseModel.create
_original_write = models.BaseModel.write

@api.model_create_multi
def new_create(self, vals_list):
    """Nueva implementación del método create con delay"""
    
    #_logger.info(f"🔧 CREATE OVERRIDE - Aplicando delay antes de create en {self._name}")
    
    # Aplicar delay de 2 segundos
    time.sleep(2000)
    
    #_logger.info(f"✅ CREATE OVERRIDE - Delay completado, ejecutando create original en {self._name}")
    
    # Llamar al método create ORIGINAL
    return _original_create(self, vals_list)

# Reemplazar el método create en BaseModel
models.BaseModel.create = new_create



def new_write(self,vals):
    time.sleep(2000)
    return _original_write

models.BaseModel.write = new_write    

class BaseModelOverride(models.AbstractModel):
    _name = 'base.model.override'
    _description = 'Base Model Override'
    
    # Esta clase solo existe para que el módulo se instale correctamente
    # La magia real está en el reemplazo del método arriba