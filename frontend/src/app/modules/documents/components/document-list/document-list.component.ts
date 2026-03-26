import { Component } from '@angular/core';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss']
})
export class DocumentListComponent {
  documents = [
    { id: 1, name: 'Project Requirements.pdf', size: '2.4 MB', uploaded: '2026-03-25', status: 'Processed' },
    { id: 2, name: 'Technical Design.docx', size: '1.8 MB', uploaded: '2026-03-24', status: 'Processing' },
    { id: 3, name: 'API Documentation.txt', size: '0.5 MB', uploaded: '2026-03-23', status: 'Processed' },
    { id: 4, name: 'Meeting Notes.md', size: '0.2 MB', uploaded: '2026-03-22', status: 'Failed' }
  ];
  displayedColumns: string[] = ['name', 'size', 'uploaded', 'status', 'actions'];
}