"""
Controllers - Camada de apresentação com rotas HTTP
"""
from .customer_controller import CustomerController
from .student_controller import StudentController
from .instructor_controller import InstructorController

__all__ = ["CustomerController", "StudentController", "InstructorController"]
