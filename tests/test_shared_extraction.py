import unittest

from shared import extraer_cuartos, extraer_departamento, extraer_descripcion, extraer_superficie_m2


class TerrainExtractionTests(unittest.TestCase):
    def test_extracts_m2_from_m2Terrain(self):
        item = {"m2Terrain": 450}
        self.assertEqual(extraer_superficie_m2(item), 450)

    def test_converts_hectares_to_m2(self):
        item = {"hectares": 0.5}
        self.assertEqual(extraer_superficie_m2(item), 5000)

    def test_extracts_department_from_locations(self):
        item = {"locations": {"state": [{"name": "Maldonado"}]}}
        self.assertEqual(extraer_departamento(item), "Maldonado")

    def test_extracts_bedrooms(self):
        item = {"bedrooms": 2}
        self.assertEqual(extraer_cuartos(item), 2)

    def test_extracts_description(self):
        item = {"description": "Apartamento luminoso"}
        self.assertEqual(extraer_descripcion(item), "Apartamento luminoso")


if __name__ == "__main__":
    unittest.main()
