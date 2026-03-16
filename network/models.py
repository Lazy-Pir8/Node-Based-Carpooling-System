from django.db import models

# Create your models here.

class Node(models.Model):
    point = models.CharField(max_length=100)

    def __str__(self):
        return self.point

class Edge(models.Model):
    from_node = models.ForeignKey(Node, related_name = "from_node", on_delete=models.CASCADE)
    to_node = models.ForeignKey(Node, related_name = "to_node", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.from_node} to {self.to_node}"
